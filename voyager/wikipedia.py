

import pandas as pd
import numpy as np
import csv
import re
import requests
import requests_cache
from bs4 import BeautifulSoup


from voyager.config import CACHE_DIR, logger
from voyager.utils import years_to_range

# Get expeditions from wikipedia
# https://en.wikipedia.org/wiki/European_and_American_voyages_of_scientific_exploration


class Wikipedia():

    csv_file = CACHE_DIR / 'wikipedia.csv'

    def __init__(self):

        self.df = self._parse()
        # try:
        #     self.df = pd.read_csv(self.csv_file)
        # except FileNotFoundError:
        #     self.df = self._parse()
        #     self.df.to_csv(self.csv_file)

    def find_voyage(self, vessel, year_from, year_to):

        df = self.df[self.df['vessels'].apply(
            lambda x: vessel in x)]

        year_range = set(years_to_range(year_from, year_to))

        for i, row in df.iterrows():
            voyage_year_range = set(years_to_range(
                row['year_from'], row['year_to']))

            # Do the years overlap
            if year_range.intersection(voyage_year_range):
                return row.to_dict()

    def _parse(self):
        r = requests.get(
            'https://en.wikipedia.org/wiki/European_and_American_voyages_of_scientific_exploration')

        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        toc = soup.find(id='toc')

        toc_section = toc.find('li', attrs={'class': 'tocsection-3'})

        voyages = []
        re_role = re.compile(
            r'naturalist|botanist|gardener|anthropologist|biologist|zoologist', re.IGNORECASE)

        re_year_range = re.compile(r'(\([cor\d–\s\?\.]+\))')

        re_comma_or_and = re.compile(r",|\sand\s")

        # Strings to remove
        collector_replacements = [
            '.',
            'assisted by',
            'the father',
            '(Le Géographe)',
            '(left the expedition to Mauritius)',
            'followed by',
            'until April 1832',
            '(second voyage)',
            '(first voyage)',
            'as Assistant Surgeon-zoologist',
            '(botanist)'
        ]

        for li in toc_section.find_all('li', attrs={'class': 'toclevel-3'}):

            collectors = set()
            href_id = li.find('a').get('href').replace('#', '')
            toctext = li.find('span', attrs={'class': 'toctext'})
            tocnumber = li.find('span', attrs={'class': 'tocnumber'}).text
            vessels = [
                self._simplify_vessel_name(i.text) for i in toctext.find_all('i')]
            year_str, _ = toctext.text.split(':')

            if year_str == '1868 and 1869–1870':
                years = [1868, 1870]
            elif year_str == '1835 and 1836':
                years = [1835, 1836]
            else:
                years = year_str.split('–')
                # Make sure second year is four digits
                if len(years) == 2:
                    if len(years[1]) == 2:

                        # If only two digits take decade from previous date
                        years[1] = years[0][:2] + years[1]

                years = list(map(int, years))

            # Find the section by ID
            # print(href_id.replace('#', ''))
            voyage_section = soup.find(id=href_id).parent
            # Messy HTML
            voyage_ul = voyage_section.find_next('ul').find('li')

            voyage_lis = [li.text for li in voyage_ul.find_all('li')]
            # Only the corvette Triton
            if not voyage_lis:
                continue

            for voyage_li in voyage_lis:
                try:
                    role_title, role_text = voyage_li.split(':')
                except ValueError:
                    pass
                else:
                    if re_role.search(role_title):

                        role_text = re_year_range.sub('', role_text)
                        split_role_text = re_comma_or_and.split(role_text)

                        for replacement in collector_replacements:
                            split_role_text = [
                                t.replace(replacement, '') for t in split_role_text]

                        collectors.update([t.strip() for t in split_role_text])

            voyages.append({
                'id': tocnumber,
                'title': toctext.text,
                'vessels': vessels,
                'year_from': years[0],
                'year_to': years[-1],
                'collectors': np.array(collectors)
            })

        df = pd.DataFrame(voyages)
        df = df.set_index(['id'])
        df = self._data_corrections(df)
        return df

    @staticmethod
    def _simplify_vessel_name(name):
        # Remove L' Le etc.,
        return name.replace("L'", '').replace('La', '').strip().lower()

    def _data_corrections(self, df):

        # 1766: HMS Niger
        df.at['2.1.4', 'collectors'] = np.array(['Joseph Banks'])
        df.at['2.1.8', 'collectors'] = np.array(
            ['Joseph Banks', 'Daniel Solander'])
        df.at['2.1.28', 'collectors'] = np.array(
            ['Prosper Garnot', 'René Primevère Lesson'])
        df.at['2.1.45', 'collectors'] = np.array(
            [
                'Jacques Bernard Hombron',
                'Louis Le Breton',
                'Honoré Jacquinot',
                'Elie Jean François Le Guillou',
                'Pierre Marie Alexandre Dumoutier'
            ])
        return df
