import re

# Regex
re_last_name = re.compile(r'[a-zA-Z]{3,}')
re_parenthensis = re.compile(r'\(.*?\)')
re_esq = re.compile(r'esq', re.IGNORECASE)


def years_to_range(year_from, year_to):
    year_range = range(int(year_from), int(year_to) + 1, 1)
    return list(year_range)


def extract_surname(name):

    name = re_esq.sub('', name)

    # Remove any text in parenthesis
    name = re_parenthensis.sub('', name)
    # Get the last part of the name
    names = re_last_name.findall(name)
    try:
        return names[-1]
    except IndexError:
        pass
