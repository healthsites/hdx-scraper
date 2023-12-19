# hdx-scraper

This application is using the HDX and the Healthsites Global Mappging Project APIs to automate the process of country data extraction from healthsites and sharing to HDX platform.

See:
- [HDX Python Library API documentation](https://github.com/OCHA-DAP/hdx-python-api)
- [Healthsites API documentation](https://github.com/healthsites/healthsites/wiki/API)

for more information.

## Download
```
git clone https://github.com/healthsites/hdx-scraper.git
```

## Dependencies

The script requires `ogr2ogr` binary which is a part of the [GDAL](https://gdal.org/) package

## Installation

Open a terminal and run the installation script. This will install a virtualenv and install all the requirements.

```shell
cd hdx-scraper
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Adjust HDX environment in the `.env` file

### HDX API key
Get into HDX website and save your API in your home directory.
The full process for getting the key is well documented in the [HDX API repository](https://github.com/OCHA-DAP/hdx-python-api) : Usage -> Getting started -> Obtaining your API Key.

### Healthsites.io API Key
Obtain you API key from [Healthsites.io](https://healthsites.io) and add it to the `.env` file


### Running the script
Open a terminal and execute the following command (it takes ages, so wrap it into `screen` or similar)

```shell
python main.py
```

# Data
The generated datasets are available in hdx from this link : https://data.humdata.org/organization/healthsites