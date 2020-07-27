import click_log
import logging
from pathlib import Path

# Directories
OUTPUT_DIR = Path(__file__).parents[1] / 'output'
INPUT_DIR = Path(__file__).parents[1] / 'input'
CACHE_DIR = INPUT_DIR / '.cache'

# Source of ships logs
IMMA_DIR = INPUT_DIR / 'imma'

# Exports from ICOADS
ICOADS_DIR = INPUT_DIR / 'icoads'

DWCA_OUTPUT_DIR = OUTPUT_DIR / 'dwca'
DWCA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# OLDDDD

APP_DATA_DIR = Path(__file__).parents[1] / 'app/src/data'

# ROUTE_DIR = OUTPUT_DIR / 'routes'
CACHE_DIR.mkdir(parents=True, exist_ok=True)

VOYAGES_DIR = OUTPUT_DIR / 'voyages'
VOYAGES_DIR.mkdir(parents=True, exist_ok=True)

# # ICOADS_DIR = INPUT_DIR / 'IMMA1_R3.1.0_COMBINED'


# GEOJSON_FILE = OUTPUT_DIR / 'feature-collection.geojson'

# GBIF_DWCA = INPUT_DIR / 'GBIF/1750-1901-dwca'

# GBIF_OCCURRENCES = OUTPUT_DIR / 'gbif.csv'

# WIKIPEDIA_VOYAGES = OUTPUT_DIR / 'wikipedia.csv'

# Logging
logger = logging.getLogger(__name__)
click_log.basic_config(logger)


handler = logging.FileHandler(OUTPUT_DIR / 'error.log')
handler.setLevel(logging.ERROR)
logger.addHandler(handler)
