from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import IMMA as imma_reader
import numpy as np
from shapely.ops import nearest_points
from shapely.geometry import Point, LineString, MultiPoint
from geopy.distance import geodesic


from voyager.config import OUTPUT_DIR, VOYAGES_DIR, logger


class Route():

    # Number of days it's acceptable to have a gap in a voyage
    INTERPOLATION_MAX_DAYS = 50
    # If there's a gap greater than max_days and max_distance, do not interpolate between those points
    INTERPOLATION_MAX_DISTANCE = 250

    def __init__(self, df):
        self.df = df.sort_values(by=['datetime'])
        self.interpolated = self.interpolate()
        self.points = MultiPoint(
            [Point(p) for p in self.interpolated[['lon', 'lat']].values])

    @property
    def date_from(self):
        return self.df['datetime'].min()

    @property
    def date_to(self):
        return self.df['datetime'].max()

    @property
    def year_from(self):
        return self.df['datetime'].min().year

    @property
    def year_to(self):
        return self.df['datetime'].max().year

    def get_location_by_date(self, date):

        location = self.interpolated.loc[self.interpolated.index == date, [
            'lat', 'lon']]

        try:
            location = location.iloc[0]
        except IndexError:
            if date > self.date_to:
                logger.debug(
                    f'Occurrence dated {date} is after voyage end date {self.date_to}')
            elif date < self.date_from:
                logger.debug(
                    f'Occurrence dated {date} is before voyage start date {self.date_to}')
            else:
                # Downgraded to debug from error, as we no longer have
                # A date from journey start to journey end
                logger.info(f'Could not find location for date {date}')
        else:
            return location.tolist()

    def get_date_by_location(self, latitude, longitude):

        point = Point(float(longitude), float(latitude))
        origin, nearest = nearest_points(point, self.points)
        date = self.interpolated[
            (self.interpolated.lon == nearest.x) &
            (self.interpolated.lat == nearest.y)
        ].index[0]

        if date >= self.date_from and date <= self.date_to:
            return date

    def get_distance(self, date, latitude, longitude):
        point_on_date = self.get_location_by_date(date)
        try:
            point = (float(latitude), float(longitude))
        except ValueError:
            return np.nan

        return geodesic(point_on_date, point).kilometers

    def interpolate(self):
        df = self.df.copy()

        df['date_diff'] = (df['datetime'] - df['datetime'].shift(1)).dt.days
        df.reset_index(drop=True, inplace=True)

        interpolation_break_points = []
        for index, row in df.iterrows():

            if row['date_diff'] > self.INTERPOLATION_MAX_DAYS:
                try:
                    previous_point = (previous_row.lat, previous_row.lon)
                except NameError:
                    # Not defined on first loop
                    pass
                else:
                    point = (row.lat, row.lon)
                    previous_point = (previous_row.lat, previous_row.lon)
                    distance = geodesic(previous_point, point).kilometers
                    if distance > self.INTERPOLATION_MAX_DISTANCE:
                        interpolation_break_points.append(index)

            previous_row = row

        if interpolation_break_points:
            logger.info('Splitting voyage into %s stages.',
                        len(interpolation_break_points))

            frames = self._split_df_into_frames(df, interpolation_break_points)
            frames = [self._interpolate(f) for f in frames]
            df = pd.concat(frames)

        else:
            # Perform interpolation on the whole data frame
            df = self._interpolate(df)

        return df

    @staticmethod
    def _split_df_into_frames(df, break_points):

        frames = []
        i = 0

        for pt in break_points:
            frames.append(df.loc[i:pt-1])
            i = pt

        # If we have any left over, add them in
        if pt < df.shape[0]:
            frames.append(df.loc[pt:])

        return frames

    def _interpolate_split_antemeridian(self, df):
        # Do not interpolate over the antemeridian
        df.reset_index(drop=True, inplace=True)
        break_points = []
        for index, row in df.iterrows():
            try:
                previous_row_is_positive = abs(
                    previous_row['lon']) == previous_row['lon']
            except NameError:
                # Not defined first loop
                pass
            else:
                row_is_positive = abs(row['lon']) == row['lon']
                if row_is_positive != previous_row_is_positive:
                    break_points.append(index)

            previous_row = row

        if break_points:
            return self._split_df_into_frames(df, break_points)
        else:
            return [df]

    def _interpolate(self, df):
        frames = self._interpolate_split_antemeridian(df)
        interpolated = [self._interpolate_frame(f) for f in frames]
        return pd.concat(interpolated)

    @staticmethod
    def _interpolate_frame(df):
        df.index = df['datetime']
        df = df.drop(['datetime', 'year', 'month', 'day', 'date_diff'], axis=1)
        df = df.resample('D').mean()
        df['lat'] = df['lat'].interpolate()
        df['lon'] = df['lon'].interpolate()
        return df

    def get_section(self, date_from, date_to):

        df = self.interpolated[(self.interpolated.index >=
                                date_from) & (self.interpolated.index <= date_to)]

        if not df.empty:
            return MultiPoint([Point(p) for p in df[['lon', 'lat']].values])

    def get_coordinates(self):
        df = self.interpolated.copy()

        df.reset_index(level=0, inplace=True)
        df['timestamp'] = df.datetime.astype('int64') // 10**9
        self._normalise_antimeridian(df)
        self._normalise_outliers(df)

        # print(df[df['lon'].between(-1, 1)].head())
        # df.index = df['datetime']

        return df[['lon', 'lat', 'timestamp']]

    def _normalise_antimeridian(self, df):
        # The voyage data has 0.x and -0.x when the route crosses the antimeridian (180)
        # So these need to be normalised into +- 180 range
        # But only if preceeding/subsequent points are close to the antimeridian
        # Otherwise we'll target longitudes near the meridian

        df.reset_index(drop=True, inplace=True)
        for index, row in df[df['lon'].between(-1, 1)].iterrows():
            try:
                adjacent_rows = np.array([
                    df.iloc[index-1]['lon'],
                    df.iloc[index+1]['lon']
                ])
            except IndexError:
                continue

            dist_to_antimeridian = (180 - np.absolute(adjacent_rows)).min()
            if dist_to_antimeridian < 5:
                lon = 180 - abs(row['lon'])
                df.at[index, 'lon'] = lon

    def _normalise_outliers(self, df):
        # There are points on the route that are clearly wrong

        for column in ['lat', 'lon']:

            for index, row in df[(df[column] - df[column].shift(-1)) > 10].iterrows():
                adjacent_rows = np.absolute(np.array([
                    df.iloc[index-1][column],
                    df.iloc[index+1][column]
                ]))
                # Make sure there's little difference between the adjacent rows
                # This makes sure we target just the outlier value
                if np.diff(adjacent_rows):
                    df.at[index, column] = np.mean(adjacent_rows)

    def __repr__(self):
        return f'Voyage({self.year_from} - {self.year_to})'
