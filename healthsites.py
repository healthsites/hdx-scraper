import csv
import json
import logging
import os
import shutil
import subprocess
import requests

from datetime import datetime
from slugify import slugify
from hdx.data.dataset import Dataset
from hdx.data.resource import Resource

timestamps = []


def check_country_status_code(country):
    url = 'https://healthsites.io/api/v3/facilities/statistic/?api-key=%s&country=%s' % (
        os.environ['HS_API_KEY'], country)
    # logging.debug(url)
    return requests.get(url).status_code


def get_countries():
    logging.info('Loading list of countries from the CSV file ...')

    output = []
    not_found = []

    with open('countries.csv', 'r') as csvfile:
        datareader = csv.reader(csvfile)
        logging.info('Found %d candidates in the CSV file ...' % sum(1 for row in datareader))
        csvfile.seek(0)  # reset file reader
        for row in datareader:
            if check_country_status_code(row[0]) == 200:
                logging.info('Checking country "%s" OK' % row[0])
                output.append(row[0])
            else:
                not_found.append(row[0])
                logging.info('Checking country "%s" NOT FOUND' % row[0])

    logging.warning('Following countries were not found: %s' % not_found)

    return output


def fetch_country_data_from_healthsites(country):
    has_result = True

    query_params = {
        'api-key': os.environ['HS_API_KEY'],
        'country': country,
        'flat-properties': True,
        'output': 'geojson',
        'page': 0
    }

    combined = {
        'type': 'FeatureCollection',
        'features': []
    }

    while has_result:
        query_params['page'] += 1
        response = requests.get('https://healthsites.io/api/v3/facilities/', params=query_params)
        data = json.loads(response.text)

        logging.info('Fetching page %d for country %s, %d records found' % (
            query_params['page'], country, len(data['features'])))

        if len(data['features']) < 100:
            has_result = False

        for record in data['features']:
            if record['properties']['changeset_timestamp']:
                timestamps.append(datetime.fromisoformat(record['properties']['changeset_timestamp']))
            combined['features'].append(record)

    shutil.rmtree('/tmp/hdx')  # clear folder from previous run
    os.mkdir('/tmp/hdx')

    logging.info('Found total of %d records for %s' % (len(combined['features']), country))

    country_slug = slugify(country).lower()

    logging.info('Saving /tmp/hdx/%s.geojson file' % country_slug)
    with open('/tmp/hdx/%s.geojson' % country_slug, 'w') as c:
        json.dump(combined, c)

    logging.info('Creating /tmp/hdx/%s.csv file' % country_slug)
    subprocess.run(['ogr2ogr', '-skipfailures', '-f', 'CSV', '/tmp/hdx/%s.csv' % country_slug, '-lco', 'GEOMETRY=AS_XY',
                    '/tmp/hdx/%s.geojson' % country_slug], capture_output=True)

    if not os.path.exists('/tmp/hdx/shapefiles'):
        os.mkdir('/tmp/hdx/shapefiles')

    subprocess.run(['ogr2ogr', '-nlt', 'POINT', '-skipfailures', '/tmp/hdx/shapefiles/%s.shp' % country_slug,
                    '/tmp/hdx/%s.geojson' % country_slug], capture_output=True)

    logging.info('Creating /tmp/hdx/%s-shapefiles.zip file' % country_slug)
    subprocess.run(['zip', '-r', '%s-shapefiles.zip' % country_slug, 'shapefiles/'], cwd='/tmp/hdx',
                   capture_output=True)

    shutil.rmtree('/tmp/hdx/shapefiles')


def fetch_hxl_data_from_healthsites(country):
    has_result = True

    query_params = {
        'api-key': os.environ['HS_API_KEY'],
        'tag-format': 'hxl',
        'country': country,
        'flat-properties': True,
        'output': 'geojson',
        'page': 0
    }

    combined = {
        'type': 'FeatureCollection',
        'features': []
    }

    while has_result:
        query_params['page'] += 1
        response = requests.get('https://healthsites.io/api/v3/facilities/', params=query_params)
        data = json.loads(response.text)

        logging.info('Fetching page %d for country %s with HXL tags, %d records found' % (
            query_params['page'], country, len(data['features'])))

        if len(data['features']) < 100:
            has_result = False

        for record in data['features']:
            combined['features'].append(record)

    logging.info('Found total of %d records with HXL tags for %s' % (len(combined['features']), country))

    country_slug = slugify(country).lower()

    logging.info('Saving /tmp/hdx/%s_hxl.geojson file' % country_slug)
    with open('/tmp/hdx/%s_hxl.geojson' % country_slug, 'w') as c:
        json.dump(combined, c)

    logging.info('Creating /tmp/hdx/%s_hxl.csv file' % country_slug)
    subprocess.run(
        ['ogr2ogr', '-skipfailures', '-f', 'CSV', '/tmp/hdx/%s_hxl.csv' % country_slug, '-lco', 'GEOMETRY=AS_XY',
         '/tmp/hdx/%s_hxl.geojson' % country_slug], capture_output=True)


def create_resource_config(country, file):
    config = {}

    if file.endswith('hxl.geojson'):
        config['name'] = slugify('%s healthsites HXL geojson' % country).lower()
        config['format'] = 'geojson'
        config['description'] = '%s healthsites geojson with HXL tags' % country
    elif file.endswith('geojson'):
        config['name'] = slugify('%s healthsites geojson' % country).lower()
        config['format'] = 'geojson'
        config['description'] = '%s healthsites geojson' % country
    elif file.endswith('hxl.csv'):
        config['name'] = slugify('%s healthsites CSV with HXL tags' % country).lower()
        config['format'] = 'csv'
        config['description'] = '%s healthsites CSV with HXL tags' % country
    elif file.endswith('csv'):
        config['name'] = slugify('%s healthsites CSV' % country).lower()
        config['format'] = 'csv'
        config['description'] = '%s healthsites CSV' % country
    elif file.endswith('zip'):
        config['name'] = slugify('%s healthsites SHP' % country).lower()
        config['format'] = 'zipped shapefile'
        config['description'] = '%s healthsites shapefiles' % country

    return config


def create_resources(country):
    output = []

    directory = '/tmp/hdx'

    for filename in os.listdir(directory):
        file = os.path.join(directory, filename)

        if os.path.isfile(file):
            config = create_resource_config(country, file)
            logging.info('Processing file %s' % file)
            # logging.info(config)
            resource = Resource()
            resource['name'] = config['name']  # i.e. 'country-healthsites-geojson'
            resource['format'] = config['format']  # i.e. 'geojson'
            resource['url'] = 'https://healthsites.io/'
            resource['description'] = config['description']
            resource.set_file_to_upload(file)

            resource.check_required_fields(['group', 'package_id'])
            output.append(resource)

    return output


def remove_current_resources(country):
    dataset = Dataset.read_from_hdx(slugify('%s healthsites' % country).lower())

    while True:
        resources = dataset.get_resources()

        if len(resources) == 0:
            break

        for resource in resources:
            logging.info('deleting previously uploaded resource %s' % resource['name'])
            dataset.delete_resource(resource)

    pass


def generate_dataset(country):
    global timestamps
    timestamps.clear()
    remove_current_resources(country)
    fetch_country_data_from_healthsites(country)
    fetch_hxl_data_from_healthsites(country)

    dataset = Dataset({
        'name': slugify("%s Healthsites" % country).lower(),
        'title': "%s Healthsites" % country,
    })

    resources = create_resources(country)

    for resource in resources:
        dataset.add_update_resource(resource)

    timestamps.sort()
    if len(timestamps):
        dataset.set_time_period(timestamps[0], timestamps[-1])

    return dataset
