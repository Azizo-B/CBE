import csv
import sqlite3
import zipfile
from functools import lru_cache, wraps
from importlib.resources import as_file, files
from io import TextIOWrapper

import pandas as pd


def cache(func):
    @wraps(func)  # Preserves the original function's metadata (docstring, name, etc.)
    @lru_cache(maxsize=512)  # Apply LRU cache to the wrapper
    def wrapper(*args, **kwargs):  # Accepts all arguments passed to the original function
        return func(*args, **kwargs)  # Call the original function with the arguments

    return wrapper


class CBEOpenData:
    """
    A class to interact with CBE (Crossroads Bank for Enterprises) Open Data files.

    This class provides methods to load, query, and analyze CBE Open Data, which contains information about
    enterprises, establishments, and their associated data (e.g., addresses, activities, contacts, etc.).
    The data is typically provided in a ZIP file containing CSV files, which are loaded into an SQLite database
    for efficient querying.

    The class supports:
    - Loading data from a local ZIP file.
    - Querying enterprise details, denominations, addresses, activities, contacts, and more.
    - Replacing code-based fields with their human-readable descriptions using CBE code tables.
    - Mimicking the data structure available on the CBE Public Search website.

    Links:
    - CBE Open Data Portal: https://kbopub.economie.fgov.be/kbo-open-data/
    - CBE Public Search: https://kbopub.economie.fgov.be/kbopub/zoeknummerform.html
    - CBE Extra Info: https://economie.fgov.be/nl/themas/ondernemingen/kruispuntbank-van/diensten-voor-iedereen/hergebruik-van-publieke

    Attributes:
        zip_path (str): Path to the ZIP file containing CBE Open Data.
        db_path (str): Path to the SQLite database (defaults to in-memory database).
        schema_path (str): Path to the SQL schema file for creating database tables.
        force_load (bool): Whether to force reloading of data even if it already exists in the database.
        db_conn (sqlite3.Connection): Connection to the SQLite database.
        zip_file (zipfile.ZipFile): Handle to the opened ZIP file.


    Methods:
        __init__: Initializes the CBEOpenData instance and loads data into the database.
        query: Executes a generic SQL query on the database.
        get_code: Fetches a code table entry for a given category, code, and language.
        get_denominations: Retrieves denominations for a given entity.
        get_addresses: Retrieves addresses for a given entity.
        get_contacts: Retrieves contacts for a given entity.
        get_activities: Retrieves activities for a given entity.
        get_branches: Retrieves branches for a given enterprise.
        get_establishments: Retrieves establishments for a given enterprise.
        get_enterprise: Retrieves enterprise details with code-based fields replaced by descriptions.
        search: Retrieves all information tied to an enterprise number, mimicking the CBE Public Search website.

    Example:
        >>> cbe_open_data = CBEOpenData(
                zip_path='KboOpenData_0133_2025_03_Full.zip',
                db_path='cbe_open_data.db',
                force_load=True
            )
        >>> enterprise_info = cbe_open_data.search("1234.567.890")
        >>> print(enterprise_info)

    Notes:
        - The class uses an LRU cache to optimize repeated queries.
        - Ensure the schema file is correctly configured to match the CSV file structure.
    """

    REQUIRED_FILES = {
        "activity.csv",
        "address.csv",
        "branch.csv",
        "code.csv",
        "contact.csv",
        "denomination.csv",
        "enterprise.csv",
        "establishment.csv",
        "meta.csv",
    }

    def __init__(self, zip_path: str, db_path: str = ":memory:", force_load: bool = False, schema_path: str = None):
        """
        Initialize the CBEOpenData instance.

        Args:
            zip_path (str): Path to the ZIP file.
            db_path (str, optional): Path to the SQLite database. Defaults to `:memory:`.
            force_load (bool, optional): Whether to force data reload. Defaults to `False`.
            schema_path (str, optional): Path to the SQL schema file. Defaults to the packaged `schema.sql`.
        """
        self.zip_path = zip_path
        self.zip_file = zipfile.ZipFile(self.zip_path, "r")
        self.db_path = db_path
        self.force_load = force_load
        self.schema_path = schema_path or self._get_default_schema_path()
        self.db_conn = sqlite3.connect(self.db_path)
        self.db_conn.row_factory = sqlite3.Row  # Enable row access by column name
        self.db_conn.execute("PRAGMA journal_mode = OFF;")
        self.db_conn.execute("PRAGMA synchronous = 0;")
        self.db_conn.execute("PRAGMA locking_mode = EXCLUSIVE;")
        self.db_conn.execute("PRAGMA temp_store = MEMORY;")

        # Validate required files
        zip_contents = set(self.zip_file.namelist())
        missing_files = self.REQUIRED_FILES - zip_contents
        if missing_files:
            raise FileNotFoundError(f"Missing required files in ZIP: {', '.join(missing_files)}")

        with self.zip_file.open("meta.csv") as meta_file:
            reader = csv.DictReader(TextIOWrapper(meta_file, encoding="utf-8"))

            # Find ExtractNumber
            self.extract_number = -1  # Default if not found
            for row in reader:
                if row.get("Variable") == "ExtractNumber":
                    self.extract_number = int(row["Value"])
                    break  # No need to read further

        # Check if the meta table exists and if the extract number matches
        if not self._should_load_data():
            print("Warning: Skipping data loading because the extract number matches and force_load=False.")
            print("Info: To force a reload of the data, set force_load=True.")
            return

        self._load_schema()

        # Load CSV data from the ZIP file
        for csv_name in self.zip_file.namelist():
            if csv_name.endswith(".csv"):
                print(f"Loading {csv_name}...")
                self._load_csv_file(csv_name)

    def _get_default_schema_path(self) -> str:
        """Get the default schema path from the package."""
        schema_resource = files("cbe").joinpath("schema.sql")
        with as_file(schema_resource) as schema_file:
            return str(schema_file)

    def _should_load_data(self) -> bool:
        """
        Check if the data should be loaded based on the extract number and force_load flag.

        Returns:
            bool: True if data should be loaded, False otherwise.
        """
        cursor = self.db_conn.cursor()

        # Check if the meta table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meta';")
        meta_table_exists = cursor.fetchone() is not None

        if not meta_table_exists:
            print("Warning: The meta table does not exist. Data will be loaded.")
            return True

        # Get the current extract number from the meta table
        cursor.execute("SELECT Value FROM meta WHERE Variable = 'ExtractNumber';")
        row = cursor.fetchone()

        if not row:
            print("Warning: No extract number found in the meta table. Data will be loaded.")
            return True

        current_extract_number = int(row["Value"])

        # Check if the extract number matches
        if self.extract_number is not None and current_extract_number == self.extract_number:
            # Matched but check if force_load is True
            if self.force_load:
                print("Warning: Extract number matches, but force_load is True. Data will be reloaded.")
                return True
            else:
                return False  # Skip loading
        else:
            print(
                (
                    "Warning: Extract number mismatch. "
                    f"Current: {current_extract_number}, Requested: {self.extract_number}. "
                    "Data will be loaded."
                )
            )
            return True

    def _load_schema(self) -> None:
        """Load SQL statements from a schema file and execute them to create tables and indexes."""
        with open(self.schema_path, "r", encoding="utf-8") as file:
            sql_script = file.read()

        print("Creating SQL tables")
        with self.db_conn:
            self.db_conn.executescript(sql_script)

    def _load_csv_file(self, csv_name: str) -> None:
        """Load CSV file into the respective table."""
        table_name = csv_name.split(".")[0]

        # Read the CSV file in chunks to avoid loading the entire file into memory
        chunk_iter = pd.read_csv(
            self.zip_file.open(csv_name),
            chunksize=1000000,  # Adjust chunk size based on memory constraints
            dtype=str,  # Ensure all data is treated as strings
            keep_default_na=False,  # Avoid interpreting empty strings as NaN
        )

        rows_affected = 0
        # Process each chunk
        for chunk in chunk_iter:

            # Append to the existing table
            rows_affected += chunk.to_sql(
                name=table_name,
                con=self.db_conn,
                if_exists="append",
                index=False,  # Don't write row indices to the database
            )

        print(f"Successfully loaded {rows_affected} rows from {csv_name} into {table_name}")

    def __del__(self) -> None:
        """Clean up resources when instance is destroyed."""
        print("Cleaning up resources...")
        if hasattr(self, "db_conn") and self.db_conn:
            print("Closing database connection")
            self.db_conn.close()
        if hasattr(self, "zip_file") and self.zip_file:
            print("Closing ZIP file")
            self.zip_file.close()

    @cache
    def query(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Generic query method."""
        cursor = self.db_conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    @cache
    def get_code(self, category: str, code: str, language: str = "NL") -> dict:
        """
        Fetch the code table entry for a given category, code, and language.

        Args:
            category (str): The category of the code (e.g., "Status", "JuridicalSituation").
            code (str): The code to look up.
            language (str): The language of the description (default is "NL" for Dutch).

        Returns:
            dict: A dictionary containing the code, language, and description.
        """
        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT Code, Language, Description FROM code WHERE Category = ? AND Code = ? AND Language = ?;", (category, code, language)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    @cache
    def get_denominations(self, entity_number: str, language: str = "NL") -> list:
        """
        Retrieve denominations for a given entity (enterprise or establishment).

        Args:
            entity_number (str): The entity number (enterprise or establishment number).
            language (str): The language for code table descriptions.

        Returns:
            list: A list of denominations with code table lookups applied.
        """
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM denomination WHERE EntityNumber = ?;", (entity_number,))
        denominations = []
        for row in cursor.fetchall():
            row = dict(row)
            row["Language"] = self.get_code("Language", row["Language"], language)
            row["TypeOfDenomination"] = self.get_code("TypeOfDenomination", row["TypeOfDenomination"], language)
            denominations.append(row)

        return denominations

    @cache
    def get_addresses(self, entity_number: str, language: str = "NL") -> list:
        """
        Retrieve addresses for a given entity (enterprise or establishment).

        Args:
            entity_number (str): The entity number (enterprise or establishment number).
            language (str): The language for code table descriptions.

        Returns:
            list: A list of addresses with code table lookups applied.
        """
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM address WHERE EntityNumber = ?;", (entity_number,))
        addresses = []
        for row in cursor.fetchall():
            row = dict(row)
            row["TypeOfAddress"] = self.get_code("TypeOfAddress", row["TypeOfAddress"], language)
            addresses.append(row)

        return addresses

    @cache
    def get_contacts(self, entity_number: str, language: str = "NL") -> list:
        """
        Retrieve contacts for a given entity (enterprise or establishment).

        Args:
            entity_number (str): The entity number (enterprise or establishment number).
            language (str): The language for code table descriptions.

        Returns:
            list: A list of contacts with code table lookups applied.
        """
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM contact WHERE EntityNumber = ?;", (entity_number,))
        contacts = []
        for row in cursor.fetchall():
            row = dict(row)
            row["EntityContact"] = self.get_code("EntityContact", row["EntityContact"], language)
            row["ContactType"] = self.get_code("ContactType", row["ContactType"], language)
            contacts.append(row)

        return contacts

    @cache
    def get_activities(self, entity_number: str, language: str = "NL") -> list:
        """
        Retrieve activities for a given entity (enterprise or establishment).

        Args:
            entity_number (str): The entity number (enterprise or establishment number).
            language (str): The language for code table descriptions.

        Returns:
            list: A list of activities with code table lookups applied.
        """
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM activity WHERE EntityNumber = ?;", (entity_number,))
        activities = []
        for row in cursor.fetchall():
            row = dict(row)
            row["ActivityGroup"] = self.get_code("ActivityGroup", row["ActivityGroup"], language)
            row["Classification"] = self.get_code("Classification", row["Classification"], language)
            nace_version = row["NaceVersion"]
            nace_code = row["NaceCode"]
            if nace_version == "2003":
                row["NaceCode"] = self.get_code("Nace2003", nace_code, language)
            elif nace_version == "2008":
                row["NaceCode"] = self.get_code("Nace2008", nace_code, language)
            elif nace_version == "2025":
                row["NaceCode"] = self.get_code("Nace2025", nace_code, language)
            activities.append(row)

        return activities

    @cache
    def get_branches(self, enterprise_number: str) -> list:
        """
        Retrieve branches for a given enterprise.

        Args:
            enterprise_number (str): The enterprise number in the format 'XXXX.XXX.XXX'.

        Returns:
            list: A list of branches.
        """
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM branch WHERE EnterpriseNumber = ?;", (enterprise_number,))
        return [dict(row) for row in cursor.fetchall()]

    @cache
    def get_establishments(self, enterprise_number: str, language: str = "NL") -> list:
        """
        Retrieve establishments for a given enterprise, including their addresses and denominations.

        Args:
            enterprise_number (str): The enterprise number in the format 'XXXX.XXX.XXX'.
            language (str): The language for code table descriptions.

        Returns:
            list: A list of establishments with their addresses and denominations.
        """
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM establishment WHERE EnterpriseNumber = ?;", (enterprise_number,))
        establishments = []
        for row in cursor.fetchall():
            establishment = dict(row)
            establishment["addresses"] = self.get_addresses(establishment["EstablishmentNumber"], language)
            establishment["denominations"] = self.get_denominations(establishment["EstablishmentNumber"], language)
            establishment["contacts"] = self.get_contacts(establishment["EstablishmentNumber"], language)
            establishments.append(establishment)

        return establishments

    @cache
    def get_enterprise(self, enterprise_number: str, language: str = "NL") -> dict:
        """
        Retrieve enterprise details and replace code-based fields with their descriptions.

        Args:
            enterprise_number (str): The enterprise number in the format 'XXXX.XXX.XXX'.
            language (str): The language for code table descriptions.

        Returns:
            dict: A dictionary containing enterprise details with code table lookups applied.
        """
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM enterprise WHERE EnterpriseNumber = ?;", (enterprise_number,))
        enterprise = cursor.fetchone()
        if enterprise:
            enterprise = dict(enterprise)
            enterprise["Status"] = self.get_code("Status", enterprise["Status"], language)
            enterprise["JuridicalSituation"] = self.get_code("JuridicalSituation", enterprise["JuridicalSituation"], language)
            enterprise["TypeOfEnterprise"] = self.get_code("TypeOfEnterprise", enterprise["TypeOfEnterprise"], language)
            if enterprise["JuridicalForm"]:
                enterprise["JuridicalForm"] = self.get_code("JuridicalForm", enterprise["JuridicalForm"], language)

        return enterprise

    @cache
    def search(self, enterprise_number: str, language: str = "NL") -> dict:
        """
        Retrieve all information tied to an enterprise number, including enterprise details, denominations, addresses,
        establishments, contacts, activities, and branches. This function mimics the data structure and details
        available on the CBE Public Search website (https://kbopub.economie.fgov.be/kbopub/zoeknummerform.html).

        The function replaces code-based fields (e.g., Status, JuridicalSituation, TypeOfEnterprise) with their
        corresponding descriptions from the CBE code tables, based on the specified language.

        Args:
            enterprise_number (str): The enterprise number in the format 'XXXX.XXX.XXX'.
            language (str): The language for code table descriptions (e.g., "NL", "FR", "DE", "EN").

        Returns:
            dict: A dictionary containing all information tied to the enterprise, with code table lookups applied.
        """
        enterprise_data = self.get_enterprise(enterprise_number, language)

        if not enterprise_data:
            raise ValueError(f"Enterprise '{enterprise_number}' not found.")

        enterprise_data.update(
            {
                "EnterpriseNumber": enterprise_number,
                "denominations": self.get_denominations(enterprise_number, language),
                "addresses": self.get_addresses(enterprise_number, language),
                "establishments": self.get_establishments(enterprise_number, language),
                "contacts": self.get_contacts(enterprise_number, language),
                "activities": self.get_activities(enterprise_number, language),
                "branches": self.get_branches(enterprise_number),
            }
        )

        return enterprise_data
