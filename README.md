# Voyager

This library analyses GBIF marine occurrence records against historical ships log data from ICOADS and OldWeather, to correct missing geospatial data (collection event date, latitude and longitude).  

A CLI interface performs these analyses and outputs a DarwinCore archive file for each identified voyage and occurrences collected on the expedition. Detailed instructions for the CLI is provided below. 

A React/DeckGL app is included with the CLI, to visualise the voyages and explore occurrences collected on each trip. 

<img alt="Data Visualisation" src="https://raw.githubusercontent.com/benscott/voyager/master/input/screenshot.png" width="500" />

## Data Visualisation - `.\app`

### `yarn start`

Runs the app in the development mode.<br />
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.<br />
You will also see any lint errors in the console.

### `yarn test`

Launches the test runner in the interactive watch mode.<br />

### `yarn build`

Builds the app for production to the `build` folder.<br />




## Data Analysis CLI

### Installation

#### 1. Clone the repository

```
git clone https://github.com/benscott/voyager.git
```

#### 2. Create conda anvironment

```
conda env create -f environment.yml
```

#### 3. Activate conda anvironment

```
conda activate voyager
```

#### 4. Run setup.py
```
python setup.py install
```

### Data Sources

#### 1.GBIF

Download occurrences from GBIF as a Darwin Core Acrhive (NOTE: this will not work with the 'Simple' data export.)

https://www.gbif.org/occurrence/search

To save time running these scripts, it is recommended a subset of GBIF data is downloaded, with dates matching those of the voyages to be analysed. For example, the visualisation uses records collected from 1750 to 1901.


#### 2. ICOADS

Data from the International Comprehensive Ocean-Atmosphere Data Set (ICOADS) is available to download from 
in International Maritime Meteorological Archive (IMMA) Format.

These are organised by month and year, and it is recommended only including the years matching the time period to be analysed. Each monthly `.imma` file should be placed in a directory together. 

#### 3. Old Weather

Some Old Weather .imma files are included in this repsository, and many others can be found on https://github.com/oldweather (place any additional in directory `input/imma`). 

The records from Old Weather is included in the ICOADS dataset but inclusion of the vessel name is patchy, so using these is recommended.

#### 3. Configuration

The location of these data sources can be configured in `voyager/config.py`.


## CLI Interface

Voyager provides three CLI interfaces

#### 1. analyse

Analyse GBIF occurrences, against IMMA Marine Observations. Outputs DwC-A.

```
voyager-cli analyse --limit 5
```

#### 2. icoads-search

Search ICOADS data for vessels.


```
voyager-cli icoads-search --vessel-name Triton --years 1880-1882
```

#### 3. icoads-to-imma

Export ICOADS log data as an IMMA file for an indivual vessel.


```
voyager-cli icoads-to-imma --vessel-name Triton --years 1880-1882
```


#### 4. app

Convert DwC-A into javascript source files, for the data visulisation react app. 

```
voyager-cli app --vessel-name challenger
```


