# adsb_json

Extract Features from OpenStreetMap (OSM) PBF files into feature-specific, named GeoPackage Files.

Please read https://tech.marksblogg.com/global-flight-tracking-adsb.html for instructions on download adsb.lol's daily ADS-B feed.

## Installation

The following should work on Ubuntu and Ubuntu for Windows.

```bash
$ sudo apt update
$ sudo apt install \
    pigz \
    python3-pip \
    python3-virtualenv

$ virtualenv ~/.adsb
$ source ~/.adsb/bin/activate

$ git clone https://github.com/marklit/adsb_json ~/adsb_json
$ python -m pip install -r ~/adsb_json/requirements.txt
```

If you're using a Mac, install [Homebrew](https://brew.sh/) and then run the following.

```bash
$ brew install \
    git \
    virtualenv

$ virtualenv ~/.adsb
$ source ~/.adsb/bin/activate
$ python -m pip install -r requirements.txt

$ git clone https://github.com/marklit/adsb_json ~/adsb_json
$ python -m pip install -r ~/adsb_json/requirements.txt
```

## Usage Example

The following should produce 25 enriched, GZIP-compressed JSON files.

```bash
$ python main.py v2024.05.26-planes-readsb-prod-0.tar
```

## Upgrading Dependencies

This project uses DuckDB which has had significant improvements between each of its releases. These releases happen every few weeks to months so it is worth keeping it, as well as the other dependencies, up to date.

If you already have a virtual environment installed then every few weeks, run the following to update the dependencies.

```bash
$ pip install -Ur requirements.txt
```
