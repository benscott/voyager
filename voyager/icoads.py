import re
import IMMA
import pandas as pd

from voyager.config import INPUT_DIR, VOYAGES_DIR, logger


class ICOADS():

    ICOADS_DIR = INPUT_DIR / 'IMMA1_R3.1.0_COMBINED'

    def get_ship_ids(self, ship_name, years):

        ship_ids = set()
        re_search = re.compile(ship_name, re.IGNORECASE)

        for year in years:
            for record in self._read_imma(year):
                supd = record.get('SUPD')
                if not supd:
                    continue
                m = re_search.search(supd)
                if m:
                    ship_ids.add(record['ID'].strip())

        return ship_ids

    def _route_analysis_by_ship_id(self, ship_name, df):
        # A report

        groups = df.groupby(by='ship_id')
        report = []
        for ship_id, group in groups:

            group = group.sort_values(by=['datetime'])

            group['date_diff'] = (
                group['datetime'] - group['datetime'].shift(1))

            group = group.sort_values(by=['date_diff'], ascending=False)

            start = group[group.datetime == group.datetime.min()].iloc[0]
            end = group[group.datetime == group.datetime.max()].iloc[0]
            # print(start.datetime)
            report.append({
                'ship_name': ship_name,
                'ship_id': ship_id,
                'start_date': start.datetime,
                'start_pos': (start.lat, start.lon),
                'end_date': end.datetime,
                'end_pos': (end.lat, end.lon),
                'num_entries': group.shape[0],
                'max_date_diff': group['date_diff'].max()
            })
        return report

    def search(self, ship_name, years):
        ship_ids = self.get_ship_ids(ship_name, years)
        if ship_ids:
            data = self._parse_imma(ship_ids, years)
            df = pd.DataFrame(data)
            df['datetime'] = pd.to_datetime(df[['day', 'year', 'month']])

            df = df.sort_values(by=['datetime'])
            df['date_diff'] = (df['datetime'] - df['datetime'].shift(1))

            # Generate new year from/to from voyage
            voyage_year_from = df['datetime'].min().year
            voyage_year_to = df['datetime'].max().year
            encoded_ship_name = ship_name.lower().replace(' ', '')
            filename = f'{encoded_ship_name}-{voyage_year_from}-{voyage_year_to}-icoads.csv'
            df.to_csv(VOYAGES_DIR / filename)

            return {
                'df': df,
                'report': self._route_analysis_by_ship_id(ship_name, df)
            }
        else:
            logger.info('No ship IDs found for %s', ship_name)

    def _parse_imma(self, ship_ids, years):
        data = []
        for year in years:
            for record in self._read_imma(year):
                try:
                    rid = record['ID'].strip()
                except AttributeError:
                    # No record ID??
                    continue

                if rid in ship_ids:
                    data.append({
                        'ship_id': rid,
                        'year': record['YR'],
                        'month': record['MO'],
                        'day': record['DY'],
                        'lat': record['LAT'],
                        'lon': record['LON']
                    })

        return data

    def _read_imma(self, year):
        for f in self.ICOADS_DIR.glob(f'IMMA1_R3.1.0_{int(year)}-*'):
            imma = IMMA.get(str(f))

            for record in imma:
                yield record
