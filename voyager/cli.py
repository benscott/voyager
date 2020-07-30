

import ast
import click
import click_log
import re
import requests
import requests_cache
from pathlib import Path
from bs4 import BeautifulSoup
import itertools
import pandas as pd
import json
from operator import attrgetter
from datetime import datetime
from dateutil.relativedelta import relativedelta
from IMMA.structure import parameters as imma_parameters
import IMMA as imma_writer

from voyager.occurrences import Occurrences
from voyager.gbif import GBIF
from voyager.icoads import ICOADS
from voyager.utils import years_to_range, extract_surname
from voyager.imma import IMMA
from voyager.wikipedia import Wikipedia
from voyager.route import Route

from voyager.config import logger, CACHE_DIR, IMMA_DIR, APP_DATA_DIR, DWCA_OUTPUT_DIR, OUTPUT_DIR

requests_cache.install_cache(str(CACHE_DIR / 'requests_cache'))

re_vessel = re.compile(r'(?P<vessel>[a-zA-Z_\+]+)_[0-9]')


@click.group()
@click.version_option()
def cli():
    pass


@cli.command()
@click_log.simple_verbosity_option(logger)
@click.option('-l', '--limit', type=int)
@click.option('-n', '--vessel-name')
def app(limit, vessel_name):

    imma_files = _cli_imma_files(vessel_name)

    counter = 0

    js_voyages_file = APP_DATA_DIR / 'voyages.js'
    js_metadata_file = APP_DATA_DIR / 'metadata.js'
    js_occurrences_file = APP_DATA_DIR / 'occurrences.js'

    map_metadata = {
        'timestamp': {
            'min': 0,
            'max': 0
        }
    }

    new_line = False

    logger.info(
        f'Exporting to {js_voyages_file}')

    def _update_map_metadata(coordinates):
        min_timestamp = coordinates.timestamp.min()
        max_timestamp = coordinates.timestamp.max()

        if min_timestamp < map_metadata['timestamp']['min']:
            map_metadata['timestamp']['min'] = min_timestamp

        if max_timestamp > map_metadata['timestamp']['max'] or not map_metadata['timestamp']['max']:
            map_metadata['timestamp']['max'] = max_timestamp

    occurrence_count = 0

    with js_voyages_file.open('w') as f:
        f.write('export default [\n')

        occurence_records = {}

        for vessel, route, dwca in _cli_get_routes(vessel_name):

            logger.info(
                f'Exporting {vessel} {route.year_from} - {route.year_to}')

            if new_line:
                f.write(',\n')

            coordinates = route.get_coordinates()

            df = dwca.copy()

            df['datetime'] = pd.to_datetime(
                df['eventDate'], infer_datetime_format=True)

            df['timestamp'] = df.datetime.astype('int64') // 10**9

            df.rename(columns={
                'gbifID': 'id',
                'scientificName': 'name',
                'decimalLatitude': 'lat',
                'decimalLongitude': 'lon',
            }, inplace=True)

            # Ensure the occurrences occur only within the published time frame
            df = df[(df['datetime'] > route.date_from) & (
                df['datetime'] <= route.date_to)]

            df = df[['timestamp', 'id', 'name', 'lat', 'lon']]

            df = df.sort_values(by=['timestamp'])
            df['timestamp'] = df['timestamp'].astype(str)

            occurrence_count += df.shape[0]
            occurence_records[vessel] = df.values.tolist()

            _update_map_metadata(coordinates)

            coordinates['timestamp'] = coordinates['timestamp'].astype(str)

            voyage = {
                'coordinates': coordinates.values.tolist(),
                'metadata': {
                    'vessel': vessel,
                    'year_from': route.year_from,
                    'year_to': route.year_to,
                    'count': df.shape[0]
                }

            }

            f.write(json.dumps(voyage))
            new_line = True

            counter += 1

            if limit and counter >= limit:
                break

        f.write('\n]')

    # Give the map tiles time to load before rendering any lines
    dt = datetime.fromtimestamp(map_metadata['timestamp']['min'])
    timestamp_min = datetime.timestamp(dt + relativedelta(months=-24))

    # Output the metadata file
    with js_metadata_file.open('w') as f:
        f.write('export default {\n')
        f.write(f"\tminTimestamp: {timestamp_min},\n")
        f.write(f"\tmaxTimestamp: {map_metadata['timestamp']['max']}")
        f.write('\n}')

    with js_occurrences_file.open('w') as f:
        f.write('export default \n')
        f.write(json.dumps(occurence_records))
        f.write('\n')

    click.secho(f'Occurrence count: {occurrence_count}', fg='green')


@ cli.command()
@ click_log.simple_verbosity_option(logger)
@ click.option('-l', '--limit', type=int)
@ click.option('-f', '--file-name')
@ click.option('-n', '--vessel-name')
def analyse(limit, file_name, vessel_name):

    if file_name:
        imma_files = [IMMA_DIR / file_name]
    else:
        imma_files = _cli_glob_files(IMMA_DIR, '*.imma', limit)

    gbif = GBIF()
    wikipedia = Wikipedia()

    total = 0

    error_totals = {}

    for imma_file in imma_files:
        vessel = _cli_imma_file_get_vessel(imma_file.stem)

        # If vessel parameter is specified
        if vessel_name and vessel_name != vessel:
            continue

        imma = IMMA(imma_file)
        route = imma.get_route()

        if route.year_to >= 1900:
            continue
        # At this point we have vessel name, and years so try and get extra metadata
        wikipedia_voyage = wikipedia.find_voyage(
            vessel, route.year_from, route.year_to)

        if wikipedia_voyage:
            collectors = [extract_surname(c)
                          for c in wikipedia_voyage['collectors'].tolist()]
        else:
            collectors = []

        expedition = None

        if vessel == 'first_fleet':
            expedition = 'first fleet'
            vessel = 'supply+sirius'

        try:
            occurrences = Occurrences(
                route, gbif, vessel=vessel, collectors=collectors, expedition=expedition
            )

            dwca_file = f'{vessel}-{route.year_from}-{route.year_to}.csv'

            occurrences.to_dwca(DWCA_OUTPUT_DIR / dwca_file)

            occurrence_stats = occurrences.get_stats()

            for error, count in occurrence_stats['errors'].items():
                error_totals.setdefault(error, 0)
                error_totals[error] += count

            total += occurrence_stats['total']

        except:
            continue

    click.secho(f'Total: {total}', fg='green')

    for error, error_total in error_totals.items():
        click.secho(f'{error}: {error_total}', fg='green')


@ cli.command()
@ click.option('-n', '--vessel-name', required=True)
@ click.option('-y', '--years', required=True)
@ click.option('-l', '--limit')
@ click_log.simple_verbosity_option(logger)
def icoads_search(vessel_name, years, limit):
    # Search ICOADS data for a vessel

    icoads = ICOADS()

    years = _cli_parse_years(years)
    result = icoads.search(vessel_name, years)

    if not result.empty:
        year_from = result['datetime'].min().year
        year_to = result['datetime'].max().year
        ship_ids = result['ship_id'].unique()
        click.secho(
            f"Log found for ID {ship_ids} - {result.shape[0]} entries {year_from}-{year_to}", fg='green')
    else:
        logger.error(f'No log records found for {vessel_name} {years}')


@ cli.command()
@ click.option('-n', '--vessel-name')
@ click.option('-y', '--years', required=True)
@ click_log.simple_verbosity_option(logger)
def icoads_to_imma(vessel_name, years):
    # Find a shape in ICOADS data, and save it to an individual IMMA file
    icoads = ICOADS()
    years = _cli_parse_years(years)
    result = icoads.search(vessel_name, years)

    if not result.empty:

        column_mappings = {
            "year": "YR",
            "month": "MO",
            "day": "DY",
            "lat": "LAT",
            "lon": "LON"
        }

        year_str = '-'.join(years)
        filepath = IMMA_DIR / f'{vessel_name}_{year_str}.imma'

        result = result.rename(columns=column_mappings)

        # Imma file has required column
        imma_required_cols = ()
        attachments = range(0, 1)
        for i in attachments:
            imma_required_cols += imma_parameters[i]

        with filepath.open("wb") as f:
            for i, row in result[column_mappings.values()].iterrows():
                record = {c: None for c in imma_required_cols}
                # Attachments dictates the required fields for the IMMA file
                record['attachments'] = list(attachments)
                record['ID'] = vessel_name

                record.update(row.to_dict())
                imma_writer.write(record, f)

        click.secho(
            f"Saved IMMA log for {vessel_name} - {result.shape[0]} entries", fg='green')

    else:

        logger.error(f'No log records found for {vessel_name} {years}')


def _cli_parse_years(years):

    year_match = re.match(r'([0-9]{4})', years)
    if year_match:
        return [year_match.group(1)]

    m = re.match(r'(?P<year_from>[0-9]{4})-(?P<year_to>[0-9]{4})', years)

    try:
        year_from = m.group('year_from')
        year_to = m.group('year_to')
    except AttributeError:
        raise click.UsageError('Please enter year range as YYYY or YYYY-YYYY')

    return years_to_range(year_from, year_to)


def _cli_get_routes(vessel_name=None):

    imma_files = _cli_imma_files()
    for imma_file in imma_files:
        vessel = _cli_imma_file_get_vessel(imma_file.stem)

        # If vessel parameter is specified
        if vessel_name and vessel_name != vessel:
            continue

        imma = IMMA(imma_file)
        route = imma.get_route()

        dwca_file_name = _cli_dwca_file_name(vessel, route)

        dwca_file = DWCA_OUTPUT_DIR / dwca_file_name
        if dwca_file.is_file():
            dwca = pd.read_csv(dwca_file)
            yield (vessel, route, dwca)


def _cli_dwca_files(limit=None):
    for f in _cli_glob_files(IDWCA_OUTPUT_DIR, '*.csv', limit):
        yield f


def _cli_imma_files(limit=None):
    for f in _cli_glob_files(IMMA_DIR, '*.imma', limit):
        yield f


def _cli_imma_files(limit=None):
    for f in _cli_glob_files(IMMA_DIR, '*.imma', limit):
        yield f


def _cli_imma_file_get_vessel(file_name):
    file_name = file_name.replace('_W1', '').replace(
        '_W2', '').replace('_C', '')
    # Extract the vessel name
    m = re_vessel.match(file_name)
    return m.group('vessel').lower()


def _cli_dwca_file_name(vessel, route):
    return f'{vessel}-{route.year_from}-{route.year_to}.csv'


def _cli_glob_files(dir_path, pattern, limit=None):
    files = list(dir_path.glob(pattern))
    if limit:
        return files[:limit]
    return files
