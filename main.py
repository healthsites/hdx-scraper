import logging
import os
import signal

from dotenv import load_dotenv
from hdx.api.configuration import Configuration

from healthsites import get_countries, generate_dataset
from utils import handler

load_dotenv()

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p', level=logging.INFO)

signal.signal(signal.SIGINT, handler)  # handle Ctrl+C


def run():
    countries = get_countries()

    conf = Configuration.create(hdx_site=os.environ['HDX_ENVIRONMENT'], user_agent="Healthsites.io")

    for country in countries:
        dataset = generate_dataset(country)
        dataset.update_from_yaml()
        dataset.add_country_location(country)
        dataset.set_expected_update_frequency('Every three months')
        dataset.add_tag('health facilities')
        dataset.set_subnational(True)
        logging.info('Uploading files to HDX for %s' % country)
        dataset.create_in_hdx()
        logging.info('Uploading files to HDX for %s done' % country)


if __name__ == "__main__":
    run()
