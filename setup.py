from pathlib import Path

from setuptools import find_packages, setup

# Read the README.md file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="cbe",
    version="0.1.6",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["requests", "pandas", "beautifulsoup4"],
    author="Aziz Baatout",
    description="Python package to work with Crossroads Bank for Enterprises (CBE)",
    keywords=["cbe", "kbo", "bce", "belgium", "open data", "public search"],
    url="https://github.com/Azizo-B/cbe",
)
