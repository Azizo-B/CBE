import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup


class CBEOpenDataPortal:
    """
    A class to interact with the CBE (Kruispuntbank van Ondernemingen) Open Data portal.

    This class provides methods to authenticate with the CBE Open Data portal, retrieve available data extracts,
    and download specific or the latest extract files. The data extracts are typically provided as ZIP files
    containing CSV files, which can be used for further processing and analysis.

    Attributes:
        BASE_URL (str): The base URL for the CBE Open Data portal.
        LOGIN_ENDPOINT (str): The endpoint for authenticating with the CBE Open Data portal.
        EXTRACT_PAGE (str): The URL of the page listing available extract files.
        EXTRACT_FILE_NAME (str): A regex pattern to parse extract file names and extract metadata.

    Methods:
        __init__: Initializes the CBEOpenDataPortal instance and logs in to the CBE Open Data portal.
        login_to_cbe: Logs into the CBE Open Data portal and returns an authenticated session.
        list_available_extracts: Retrieves a list of available extract files from the CBE Open Data portal.
        get_extract_url: Retrieves the file url of a specific or the latest CBE extract file.
        download_zip: Downloads a CBE extract file from the portal and saves it locally.

    Example:
        >>> portal = CBEOpenDataPortal(username="your_username", password="your_password")
        >>> extracts = portal.list_available_extracts()
        >>> for extract in extracts:
        ...     print(f"Extract: {extract}")
        >>> extract_url = portal.get_extract_url(extract_number="0133")
        >>> print(f"Extract Url: {extract_url}")
        >>> portal.download_zip(extract_number="0133")

    Notes:
        - The CBE Open Data portal requires authentication to access extract files.
        - The class uses the `requests` library for HTTP requests and `BeautifulSoup` for parsing HTML.
        - Extracts are identified by their extract number, year, month, and type (e.g., "Full" or "Update").
    """

    BASE_URL = "https://kbopub.economie.fgov.be/kbo-open-data"
    LOGIN_ENDPOINT = f"{BASE_URL}/static/j_spring_security_check"
    # HTML page with the extract files listed
    EXTRACT_PAGE = f"{BASE_URL}/affiliation/xml/?files"
    # Files will be found at BASE_EXTRACT_URL + "/files/" + <file_name>
    BASE_EXTRACT_URL = f"{BASE_URL}/affiliation/xml"
    # Regex pattern to parse extract file names and extract metadata
    # Example file name: KboOpenData_0133_2025_03_Full.zip
    EXTRACT_FILE_NAME = r".*(?P<extract_number>\d{4})_(?P<year>\d{4})_(?P<month_num>\d{2})_.*(?P<extract_type>Full|Update).zip"

    def __init__(self, username: str, password: str) -> None:
        self.session = self.login_to_cbe(username, password)

    @staticmethod
    def login_to_cbe(username: str, password: str) -> requests.Session:
        """
        Logs into the CBE Open Data portal and returns an authenticated session.

        Args:
            username (str): The username for logging in.
            password (str): The password for logging in.

        Returns:
            requests.Session: An authenticated session object for subsequent requests.

        Raises:
            ValueError: If authentication fails.
        """
        session = requests.Session()
        payload = {"j_username": username, "j_password": password}

        login_response = session.post(CBEOpenDataPortal.LOGIN_ENDPOINT, data=payload)
        if login_response.status_code != 200:
            raise ValueError(f"Login failed. response status {login_response.status_code}.")

        if username not in login_response.text:
            raise ValueError("Login failed. recieved unexpected response.")

        print("Login successful!")
        return session

    def list_available_extracts(self) -> list:
        """
        Retrieves available extract files from the CBE Open Data page.

        Returns:
            list: A list of dictionaries representing the available extract files.

                Each dictionary has the following keys:
                - extract_number: The extract number (e.g., "0133").
                - year: The year of the extract (e.g., "2024").
                - month_num: The month of the extract (e.g., "03").
                - extract_type: The type of the extract (e.g., "Full" or "Update").
                - file_url: The file url of the extract.

        Raises:
            ValueError: If no extracts are found at all.
        """
        response = self.session.get(self.EXTRACT_PAGE)

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all 'a' tags and filter those containing 'href' attributes
        links = soup.find_all("a", href=True)
        extracts = []
        for link in links:
            extract_match = re.match(self.EXTRACT_FILE_NAME, link["href"])

            if extract_match:
                extract = extract_match.groupdict()
                extract["file_url"] = self.BASE_EXTRACT_URL + "/" + link["href"]
                extracts.append(extract)

        if not extracts:
            raise ValueError("No extracts were found.")

        return extracts

    def get_extract_url(self, extract_number: str = None, extract_type: str = "Full") -> str:
        """
        Retrieves the file path of the CBE extract file based on the provided extract number.

        If an extract number is provided, it will return the corresponding file path,
        if not provided, it will return the latest extract found.

        Args:
            extract_number (str, optional): The extract number to find a specific extract file. If not provided,
                                             the most recent extract will be returned.
            extract_type (str, optional): The extract type, either 'Full' or 'Update'. Defaults to 'Full'.

        Returns:
            str: The file path of the requested CBE extract file.

        Raises:
            ValueError: If an extract with the specified number is not found or no extracts are found at all.
        """
        extracts = self.list_available_extracts()

        if extract_number:
            for extract in extracts:
                if extract["extract_number"] == extract_number and extract["extract_type"] == extract_type:
                    return extract["file_url"]
            raise ValueError(f"Extract of type {extract_type} with number {extract_number} was not found.")

        # Return the latest extract's file path if no extract_number was provided
        latest_extract = max(extracts, key=lambda x: datetime.strptime(f"{x['year']}{x['month_num']}", "%Y%m"))
        return latest_extract["file_url"]

    def download_zip(
        self, extract_number: str = None, extract_type: str = "Full", download_dir: str = "data", force_download: bool = False
    ) -> str:
        """
        Downloads the CBE Open Data ZIP file from the official CBE portal.

        This method downloads the ZIP file for the specified extract (or the latest one).
        The downloaded file is saved in `download_dir` with its original name (e.g., `KboOpenData_0133_2025_03_Full.zip`).

        Args:
            extract_number (str, optional): The extract number to download. Defaults to latest.
            extract_type (str, optional): The extract type, either 'Full' or 'Update'. Defaults to 'Full'.
            download_dir (str, optional): Directory to save the downloaded ZIP file. Defaults to "data".
            force_download (bool, optional): Whether to overwrite an existing file. Defaults to False.

        Returns:
            str: The path of the downloaded ZIP file.

        Raises:
            ValueError: If the download process encounters an error or if extract is not found.
        """
        # Ensure the download directory exists
        if not os.path.exists(download_dir):
            raise ValueError(f"Download directory '{download_dir}' does not exist.")

        extract_url = self.get_extract_url(extract_number, extract_type)

        file_name = extract_url.rsplit("/", 1)[-1]
        file_path = os.path.join(download_dir, file_name)

        if os.path.exists(file_path) and not force_download:
            print(f"File already exists: {file_path}. Use 'force_download=True' to overwrite.")
            return file_path

        zip_response = self.session.get(extract_url, stream=True)
        if zip_response.status_code != 200:
            raise ValueError(f"Failed to download ZIP file. Status code: {zip_response.status_code}")

        print(f"Downloading: {extract_url}")
        with open(file_path, "wb") as f:
            for chunk in zip_response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("ZIP file downloaded and saved!")
        return file_path
