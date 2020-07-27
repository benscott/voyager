import numpy as np
import pandas as pd
import re
import calendar
from datetime import datetime
from shapely.geometry import Point
from shapely.ops import nearest_points
import math

from voyager.config import logger
from voyager.utils import extract_surname
from geopy.distance import geodesic


class Occurrences():

    additional_columns = ['_error', '_distance', '_inferred_on']

    # Must be within X km on the day of the route
    MAX_KM_TO_ROUTE = 100

    pd.options.mode.chained_assignment = None

    def __init__(self, route, gbif, vessel, collectors=[], expedition=None):
        self._frames = []
        self.route = route
        self.vessel = vessel
        self.collectors = collectors
        self.expedition = expedition
        self.inferred_collectors = {}
        self.gbif = gbif.get_years(route.year_from, route.year_to)
        # Set GBIF datetime data type
        self._add_gbif_datetime()
        self._add_additional_columns()
        self.df = self._get_occurences()

        if not self.df.empty:
            self.df = self._validate_distance_to_route(self.df)

    def to_dwca(self, file_path):
        if self.df.empty:
            return

        def concatenateIssue(row):
            if row._error:
                try:
                    is_nan = math.isnan(row.issue)
                except TypeError:
                    is_nan = False
                if row.issue and not is_nan:
                    row.issue += f';{row._error}'
                else:
                    row.issue = row._error

            return row.issue

        df = self.df.copy()
        df['dynamicProperties'] = np.nan

        df['dynamicProperties'] = df.apply(
            lambda row: {
                'vessel': self.vessel,
                'distance': row['_distance'],
                'voyagerInferrences': row['_inferred_on']
            }, axis=1)

        df['issue'] = df.apply(concatenateIssue, axis=1)
        df.drop(self.additional_columns, axis=1, inplace=True)
        # We merged these in from dynamicProperties
        df.drop(['vessel', 'expedition', 'datetime'], axis=1, inplace=True)
        df.drop(df.filter(regex="Unname"), axis=1, inplace=True)
        logger.info('Saved DWC-A %s', file_path)
        df.to_csv(file_path, index=False)

    def get_stats(self):
        stats = {
            'errors': self.df['_error'].value_counts().to_dict(),
            'inferred_on':  self.df['_inferred_on'].value_counts(),
            'total': self.df.shape[0]
        }
        return stats

    def infererence_count(self):
        return self.df[self.df['_date'].notnull() | self.df['_lat'].notnull()].shape[0]

    def _add_gbif_datetime(self):
        self.gbif['datetime'] = pd.to_datetime(
            self.gbif['datetime'], infer_datetime_format=True)

    def _add_additional_columns(self):
        for column in self.additional_columns:
            self.gbif[column] = np.nan

    def _get_occurences(self):
        self._get_occurences_by_vessel()
        if self.expedition:
            self._get_occurences_by_expedition()
        if self.collectors:
            self._get_occurences_by_collector()
        if self.inferred_collectors:
            self._get_occurences_by_inferred_collector()
        self._get_occurences_by_geotemporal_proximity()

        if self._frames:
            df = pd.concat(self._frames)
            df = df.drop_duplicates(subset='gbifID', keep="last")

            logger.error('%s Occurrences with complete data',
                         df.shape[0])
            return df
        else:
            logger.error('No occurrences found for %s - %s',
                         self.vessel, self.route.year_from)

            return pd.DataFrame()

    def _get_location_by_date(self, date):
        location = self.route.get_location_by_date(date)

        # if not location:
        #     location = [np.nan, np.nan]

        return pd.Series(location)

    def _get_date_by_location(self, latitude, longitude):
        return self.route.get_date_by_location(latitude, longitude)

    def _get_occurences_by_vessel(self):

        # Match data by expedition and vessel data
        for field in ['vessel', 'expedition']:
            if self.gbif[field].any():

                if '+' in self.vessel:
                    vessels = self.vessel.split('+')
                    df = self.gbif[self.gbif[field].str.contains(
                        '|'.join(vessels), case=False, na=False, regex=True)]
                else:
                    df = self.gbif[self.gbif[field].str.contains(
                        self.vessel, case=False, na=False)]

                df['_inferred_on'] = field

                logger.info('Found %s occurences for %s.', df.shape[0], field)

                self._process_occurrences_with_inferences(df)

                # As we have matched on vessel, expedition we can be usre these collectors
                # Are correct, so update the property
                self._update_inferred_collectors(df)

    def _get_occurences_by_expedition(self):
        if self.gbif['expedition'].any():
            df = self.gbif[self.gbif['expedition'].str.contains(
                self.expedition, case=False, na=False)]

            df['_inferred_on'] = 'expedition'

            self._process_occurrences_with_inferences(df)

            # As we have matched on vessel, expedition we can be usre these collectors
            # Are correct, so update the property
            self._update_inferred_collectors(df)

    def _update_inferred_collectors(self, df):
        for name, count in df['recordedBy'].value_counts().to_dict().items():
            self.inferred_collectors.setdefault(name, 0)
            self.inferred_collectors[name] += count

    def _get_occurences_by_collector(self):

        df = self.gbif[self.gbif['recordedBy'].str.contains(
            '|'.join(self.collectors), case=False, na=False)]

        df['_inferred_on'] = 'collector'

        logger.info('Found %s occurences by collector name.', df.shape[0])

        self._process_occurrences_with_inferences(df)

    def _get_occurences_by_inferred_collector(self):

        name_blacklist = ['Anonymous', 'Unknown',
                          'Unnamed', 'Unidentified', 'Anon']

        # Number of times we should have seen a collector name for it to be included
        occurrence_threshold = 50

        collectors = [name for name, count in self.inferred_collectors.items(
        ) if count > occurrence_threshold]

        collectors = [extract_surname(c) for c in collectors]

        collectors = [c for c in collectors if c and c not in name_blacklist]
        collectors = set(collectors)

        # We do not want to search for the same collector again
        collectors = collectors.difference(set(self.collectors))

        if collectors:

            df = self.gbif[self.gbif['recordedBy'].str.contains(
                '|'.join(collectors), case=False, na=False)]

            df['_inferred_on'] = 'inferred_collector'

            logger.info(
                'Found %s occurences by inferred collector names: %s.',
                df.shape[0],
                ','.join(collectors)
            )

            self._process_occurrences_with_inferences(df)

    def _process_occurrences_with_inferences(self, df):
        if not df.empty:

            has_date_mask = df.datetime.notnull()
            has_location_mask = df['decimalLatitude'].notnull(
            ) & df['decimalLongitude'].notnull()

            # If they have both lat/lon and date, no further processing required
            with_date_location = df[has_date_mask & has_location_mask]
            logger.info('%s occurences with both date and location.',
                        with_date_location.shape[0])

            self._frames.append(with_date_location)

            # If they have a date & no lat/lng
            date_not_location = df[has_date_mask &
                                   np.logical_not(has_location_mask)].copy()

            if not date_not_location.empty:

                date_not_location['_error'] = 'COORDINATES_INFERRED'
                # We're calculating the lat/lon from the date, so distance will always be 0
                date_not_location['_distance'] = 0

                date_not_location[['decimalLatitude', 'decimalLongitude']] = date_not_location['datetime'].apply(
                    self._get_location_by_date)

                logger.info('%s occurences with date and inferred location.',
                            date_not_location.shape[0])

                self._frames.append(date_not_location)

            location_not_date = df[has_location_mask &
                                   np.logical_not(has_date_mask)].copy()

            if not location_not_date.empty:

                location_not_date['_error'] = 'RECORDED_DATE_INFERRED'

                location_not_date['datetime'] = location_not_date.apply(
                    lambda row: self._get_date_by_location(
                        row['decimalLatitude'], row['decimalLongitude']), axis=1)

                logger.info('%s occurences with location and inferred date.',
                            location_not_date.shape[0])

                self._frames.append(location_not_date)

    def _add_distance_to_route(self, df):
        # It is possible that matching on date / records that have lat/lon
        # includes records that are too distant from the route - remove these
        # And must have lat/lon
        df = df[
            df['decimalLatitude'].notnull()
            & df['decimalLongitude'].notnull()
        ]

        mask = df['_distance'].isnull()

        logger.info('Calculating distance for %s occurences.',
                    mask.sum())

        df['_distance'] = df.apply(
            lambda row: row['_distance'] if row['_distance'] >= 0 else self._calc_geodesic_distance(
                row['datetime'],
                row['decimalLatitude'],
                row['decimalLongitude']
            ),
            axis=1
        )

        return df

    def _calc_geodesic_distance(self, datetime, latitude, longitude):
        # Get nearest point on route
        return self.route.get_distance(datetime, latitude, longitude)

    def _get_occurences_by_geotemporal_proximity(self):

        # Have to have date so lets filter on date range
        df = self.gbif[
            (self.gbif.datetime >= self.route.date_from) &
            (self.gbif.datetime <= self.route.date_to)
        ]

        df = self._add_distance_to_route(df)
        df = df[df['_distance'] < self.MAX_KM_TO_ROUTE]
        df['_inferred_on'] = 'route_proximity'

        logger.info('%s occurrences found within %skm of route',
                    df.shape[0], self.MAX_KM_TO_ROUTE)

        self._frames.append(df)

    def _validate_distance_to_route(self, df):
        df = self._add_distance_to_route(df)

        # Update error if it's too far
        df.loc[df['_distance'] > self.MAX_KM_TO_ROUTE,
               ['_error']] = 'INVALID_DISTANCE_TO_ROUTE'

        return df
