

from datetime import datetime
import pandas as pd
import json


from voyager.config import INPUT_DIR, OUTPUT_DIR, CACHE_DIR, logger


class GBIF():

    GBIF_DWCA = INPUT_DIR / 'GBIF/1750-1901-dwca'

    columns = [
        'gbifID',
        'datasetKey',
        'occurrenceID',
        'kingdom',
        'phylum',
        'class',
        'order',
        'family',
        'genus',
        'species',
        'infraspecificEpithet',
        'taxonRank',
        'scientificName',
        'verbatimScientificName',
        'countryCode',
        'locality',
        'stateProvince',
        'occurrenceStatus',
        'individualCount',
        'decimalLatitude',
        'decimalLongitude',
        'coordinateUncertaintyInMeters',
        'coordinatePrecision',
        'elevation',
        'elevationAccuracy',
        'depth',
        'depthAccuracy',
        'eventDate',
        'day',
        'month',
        'year',
        'taxonKey',
        'speciesKey',
        'basisOfRecord',
        'institutionCode',
        'collectionCode',
        'catalogNumber',
        'recordNumber',
        'identifiedBy',
        'dateIdentified',
        'license',
        'rightsHolder',
        'recordedBy',
        'typeStatus',
        'establishmentMeans',
        'lastInterpreted',
        'mediaType',
        'issue',
    ]

    def __init__(self):
        # To speeds things up DWCA file will only get populated when
        # A cached file is not found
        self.dwca = None

    def get_cached(self, func, **kwargs):
        cache_key = 'gbif'

        if kwargs:
            kwargs_key = '-'.join(map(str, kwargs.values()))
            cache_key = f'{cache_key}-{kwargs_key}'

        cache_path = CACHE_DIR / f'{cache_key}.csv'

        try:
            logger.info(f'Loading {cache_key} from cache')
            df = pd.read_csv(
                cache_path
            )
        except FileNotFoundError:
            logger.info(f'Cached {cache_key} not found')

            # If we haven't yet loaded the main GBIF file, load it now
            # But only if kwargs are specified to prevent infinite loop
            if self.dwca is None and kwargs:
                logger.info(f'Loading DWCA')
                self.dwca = self.get_cached(
                    self.parse_dwca,
                )

            df = func(**kwargs)
            df.to_csv(cache_path)
        finally:
            return df

    def get_years(self, year_from, year_to):
        return self.get_cached(
            self._get_years,
            year_from=year_from,
            year_to=year_to
        )

    def _get_years(self, year_from, year_to):
        return self.dwca[(self.dwca['year'] >= year_from)
                         & (self.dwca['year'] <= year_to)]

    def parse_dwca(self):
        df = pd.read_csv(
            self.GBIF_DWCA / 'occurrence.txt',
            sep='\t',
            error_bad_lines=False,
            # usecols=self.columns,
            # nrows=100000
        )

        def _dynamic_properties_get_vessel(row):
            props_dict = self._parse_dynamic_properties(
                row['dynamicProperties'])
            return props_dict.get('vessel') or props_dict.get('ship')

        def _dynamic_properties_get_expedition(row):
            props_dict = self._parse_dynamic_properties(
                row['dynamicProperties'])
            return props_dict.get('expedition') or props_dict.get('cruise')

        def _get_datetime(row):
            try:
                dt = datetime(year=int(row['year']),
                              month=int(row['month']),
                              day=int(row['day'])
                              )
            except ValueError:
                return None
            else:
                return dt

        df['vessel'] = None
        df['expedition'] = None

        df['vessel'] = df[df['dynamicProperties'].str.contains(
            'vessel|ship', case=False, regex=True, na=False)].apply(lambda row: _dynamic_properties_get_vessel(row), axis=1)
        df['expedition'] = df[df['dynamicProperties'].str.contains(
            'expedition|cruise', case=False, regex=True, na=False)].apply(lambda row: _dynamic_properties_get_expedition(row), axis=1)

        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df['month'] = pd.to_numeric(df['month'], errors='coerce')
        df['day'] = pd.to_numeric(df['day'], errors='coerce')

        df['datetime'] = None

        date_mask = df['year'].notnull(
        ) & df['month'].notnull() & df['day'].notnull()

        df['datetime'] = df[date_mask].apply(
            lambda row: _get_datetime(row), axis=1)

        return df

    @ staticmethod
    def _parse_dynamic_properties(dynamic_props):
        props_dict = {}

        try:
            props_dict = json.loads(dynamic_props)
        except json.JSONDecodeError:
            try:
                exploded = dynamic_props.split(';')
                exploded = [e.split(':') for e in exploded]
                props_dict = {k.strip(): v.strip() for k, v in exploded}
            except ValueError:
                pass

        return props_dict
