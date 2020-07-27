# Voyager

Analyse GBIF marine occurrence records against ship logs

## Installation

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

## CLI Interface

Voyager provides three CLI interfaces

#### 1. analyse

Analyse GBIF occurrences, against IMMA Marine Observations. Outputs DwC-A.

```
voyager analyse --limit 5
```

#### 2. app

Convert DwC-A into javascriopt source files, for the data visulisation react app.

```
voyager app --vessel-name challenger
```


#### 3. icoads-search

Search ICOADS data for vessels.


```
voyager icoads-search --vessel-name challenger --years 1820-1822
```


