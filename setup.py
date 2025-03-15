from setuptools import setup, find_packages

setup(
    name="cbe",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["requests", "pandas", "beautifulsoup4", "sqlite3"],
    author="Aziz Baatout",
    description="Python package to work with Crossroads Bank for Enterprises (CBE)",
    keywords=["cbe", "kbo", "bce", "belgium", "open data", "public search"],
    url="https://github.com/yourusername/cbe",
)
