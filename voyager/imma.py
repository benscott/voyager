
import IMMA as imma_reader
import pandas as pd
from shapely.ops import nearest_points
from shapely.geometry import Point, LineString, MultiPoint
from geopy.distance import geodesic

from voyager.route import Route


class IMMA():

    # Read the IMMA file and return instance of Route()

    def __init__(self, file_path):
        self.df = self._parse_imma_file(file_path)

    @staticmethod
    def _parse_imma_file(file_path):
        route = []
        imma_records = imma_reader.get(str(file_path))

        for record in imma_records:
            route.append({
                'year': record['YR'],
                'month': record['MO'],
                'day': record['DY'],
                'lat': record['LAT'],
                'lon': record['LON']
            })

        df = pd.DataFrame(route)
        df = df.dropna()
        df['datetime'] = pd.to_datetime(df[['day', 'year', 'month']])
        return df

    def get_route(self):
        return Route(self.df)
