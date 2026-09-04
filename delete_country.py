import argparse
import logging
import os
import sys

from dotenv import load_dotenv
from hdx.api.configuration import Configuration
from hdx.data.dataset import Dataset
from hdx.data.hdxobject import HDXError
from slugify import slugify

load_dotenv()

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p', level=logging.INFO)


def delete_country(country):
    Configuration.create(hdx_site=os.environ['HDX_ENVIRONMENT'], user_agent="Healthsites.io")

    name = slugify('%s healthsites' % country).lower()
    dataset = Dataset.read_from_hdx(name)

    if dataset is None:
        logging.error('No dataset "%s" found on HDX for country %s' % (name, country))
        return False

    logging.info('Deleting dataset "%s" (%d resources) from HDX' % (name, len(dataset.get_resources())))
    try:
        dataset.delete_from_hdx()
    except HDXError as e:
        logging.error('Failed to delete dataset "%s": %s' % (name, str(e)))
        return False

    logging.info('Dataset "%s" deleted' % name)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Delete a single country dataset from HDX.')
    parser.add_argument('country', help='Country name as listed in countries.csv, e.g. "Andorra"')
    args = parser.parse_args()

    sys.exit(0 if delete_country(args.country) else 1)
