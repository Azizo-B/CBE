# CBE - Crossroads Bank for Enterprises Python Package

**GitHub Repository**: [https://github.com/Azizo-B/cbe](https://github.com/azizo-b/CBE)

The **CBE** package provides a Python interface to work with the **Crossroads Bank for Enterprises (CBE)**, also known as:

- **Kruispuntbank van Ondernemingen (KBO)** in Dutch
- **Banque-Carrefour des Entreprises (BCE)** in French
- **Zentrale Datenbank der Unternehmen (ZDU)** in German

## Features

- **Authenticate with CBE Open Data Portal**: Log in to the CBE Open Data portal using your credentials.
- **List Available Extracts**: Retrieve a list of available data extracts (e.g., Full or Update).
- **Download Extracts**: Download specific or the latest data extracts as ZIP files.
- **Load CBE Open Data**: Load data from ZIP files.
- **Efficient Querying**: Data is loaded into an SQLite database for fast and efficient querying.
- **Query Enterprise Data**: Retrieve enterprise details, denominations, addresses, activities, contacts, and more.
- **Code Table Lookups**: Replace code-based fields with human-readable descriptions using CBE code tables.
- **Public Search Mimicry**: Mimic the data structure available on the [CBE Public Search](https://kbopub.economie.fgov.be/kbopub/zoeknummerform.html) website.

## Installation

You can install the package via pip:

```bash
pip install cbe
```

## Quick Start

### **Option 1: Authenticate and Download Extracts Using Python**

You can use the `CBEOpenDataPortal` class to authenticate with the CBE Open Data portal and download the data extract directly in Python:

```python
from cbe import CBEOpenData, CBEOpenDataPortal

# Initialize the portal class
portal = CBEOpenDataPortal(username="your_username", password="your_password")

# List available extracts
extracts = portal.list_available_extracts()
for extract in extracts:
    print(f"Extract: {extract}")

# Download the latest extract
zip_path = portal.download_zip(download_dir="data")

# Initialize the CBEOpenData class with the downloaded ZIP file
cbe = CBEOpenData(zip_path=zip_path)

# Search for an enterprise
enterprise_info = cbe.search("1234.567.890")
print(enterprise_info)
```

### **Option 2: Manually Download the ZIP File**

Alternatively, you can manually download the ZIP file from the [CBE Open Data Portal](https://kbopub.economie.fgov.be/kbo-open-data/login?lang=en) and pass the path to the `CBEOpenData` class:

```python
from cbe import CBEOpenData

# Initialize the CBEOpenData class with the path to the manually downloaded ZIP file
cbe = CBEOpenData(zip_path="path/to/KboOpenData_0133_2025_03_Full.zip")

# Search for an enterprise
enterprise_info = cbe.search("1234.567.890")
print(enterprise_info)
```

## Documentation

For detailed documentation, including examples and API reference, visit the [CBE Documentation](https://Azizo-B.github.io/CBE).

## Links

- **CBE Open Data Portal**: [https://kbopub.economie.fgov.be/kbo-open-data/](https://kbopub.economie.fgov.be/kbo-open-data/)
- **CBE Public Search**: [https://kbopub.economie.fgov.be/kbopub/zoeknummerform.html](https://kbopub.economie.fgov.be/kbopub/zoeknummerform.html)
- **CBE Extra Info**: [https://economie.fgov.be/nl/themas/ondernemingen/kruispuntbank-van/diensten-voor-iedereen/hergebruik-van-publieke](https://economie.fgov.be/nl/themas/ondernemingen/kruispuntbank-van/diensten-voor-iedereen/hergebruik-van-publieke)

## Contributing

Contributions are welcome! If you'd like to contribute, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
