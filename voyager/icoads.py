import re
import IMMA
import pandas as pd

from voyager.config import INPUT_DIR, CACHE_DIR, IMMA_DIR,  logger


class ICOADS():

    ICOADS_DIR = INPUT_DIR / 'IMMA1_R3.1.0_COMBINED'

    def search(self, vessel_name, years):

        df = self._parse_imma(vessel_name, years)
        df['datetime'] = pd.to_datetime(
            df['datetime'], infer_datetime_format=True)

        return df

    def _parse_imma(self, vessel_name, years):

        cache_key = 'icoads_{0}_{1}'.format(
            vessel_name,
            '-'.join(years)
        ).lower()

        cache_path = CACHE_DIR / f'{cache_key}.csv'

        try:
            logger.info(f'Loading {cache_key} from cache')
            df = pd.read_csv(
                cache_path
            )
        except FileNotFoundError:
            logger.info(f'Cached {cache_key} not found - parsing data')
        else:
            return df

        re_search = re.compile(vessel_name, re.IGNORECASE)

        data = []
        for year in years:
            for record in self._read_imma(year):
                supd = record.get('SUPD')
                if not supd:
                    continue

                try:
                    rid = record['ID'].strip()
                except AttributeError:
                    # No record ID??
                    continue

                m = re_search.search(supd)

                if m:
                    data.append({
                        'ship_id': rid,
                        'year': record['YR'],
                        'month': record['MO'],
                        'day': record['DY'],
                        'lat': record['LAT'],
                        'lon': record['LON']
                    })

        df = pd.DataFrame(data)

        df['datetime'] = pd.to_datetime(df[['day', 'year', 'month']])
        df = df.sort_values(by=['datetime'])

        df.to_csv(cache_path)
        return df

    def _read_imma(self, year):
        for f in self.ICOADS_DIR.glob(f'IMMA1_R3.1.0_{int(year)}-*'):
            imma = IMMA.get(str(f))

            for record in imma:
                yield record
