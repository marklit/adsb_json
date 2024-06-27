#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# pylint: disable=C0116 C0209 R0916 R0912 R0915 R0914 C0201 R1732 W1514 R0913

"Enrich ADSB.lol feed and store as 1M-line, GZIP-compressed JSONL files"

from   datetime      import datetime
import json
from   shlex         import quote
import tarfile
import zlib

from   flydenity     import Parser
import h3
from   rich.progress import Progress, track
from   shpyx         import run as execute
import typer


aircraft_keys = set([
    'alert',
    'alt_geom',
    'baro_rate',
    'category',
    'emergency',
    'flight',
    'geom_rate',
    'gva',
    'ias',
    'mach',
    'mag_heading',
    'nac_p',
    'nac_v',
    'nav_altitude_fms',
    'nav_altitude_mcp',
    'nav_heading',
    'nav_modes',
    'nav_qnh',
    'nic',
    'nic_baro',
    'oat',
    'rc',
    'roll',
    'sda',
    'sil',
    'sil_type',
    'spi',
    'squawk',
    'tas',
    'tat',
    'track',
    'track_rate',
    'true_heading',
    'type',
    'version',
    'wd',
    'ws'])

app = typer.Typer(rich_markup_mode='rich')


def gzip_jsonl(filename:str):
    execute('pigz -9 -f %s' % quote(filename))


def process_records(rec,
                    num_recs:int,
                    out_filename:str,
                    out_file,
                    source_date:str,
                    verbose:bool):
    # Keep in integer form to calculate offset in trace dictionary
    timestamp        = rec['timestamp']
    rec['timestamp'] = str(datetime.utcfromtimestamp(rec['timestamp']))

    if 'year' in rec.keys() and str(rec['year']) == '0000':
        return num_recs, out_filename, out_file

    if 'noRegData' in rec.keys():
        return num_recs, out_filename, out_file

    rec['icao'] = rec['icao'].lower()

    for key in ('desc', 'r', 't', 'ownOp'):
        if key in rec.keys():
            rec[key]  = rec[key].upper()

    if 'r' in rec.keys():
        try:
            # Aircraft Registration Parser
            # WIP: contain within exception to avoid crashing part way through
            parser = Parser()
            reg_details = parser.parse(rec['r'])

            if reg_details:
                rec['reg_details'] = reg_details
        except: # pylint: disable=W0702
            pass

    for trace in rec['trace']:
        num_recs = num_recs + 1
        _out_filename = 'traces_%s_%04d.jsonl' % (source_date,
                                                  int(num_recs / 1_000_000))

        if _out_filename != out_filename:
            if out_file:
                out_file.close()

            if out_filename:
                if verbose:
                    print('Compressing %s' % out_filename)

                gzip_jsonl(out_filename)

            out_file = open(_out_filename, 'w')
            out_filename = _out_filename

        rec['trace'] = {
            'timestamp': str(datetime.utcfromtimestamp(timestamp +
                                                       trace[0])),
            'lat':                     trace[1],
            'lon':                     trace[2],
            'h3_5':                    h3.geo_to_h3(trace[1],
                                                    trace[2],
                                                    5),
            'altitude':
                trace[3]
                if str(trace[3]).strip().lower() != 'ground'
                else None,
            'ground_speed':            trace[4],
            'track_degrees':           trace[5],
            'flags':                   trace[6],
            'vertical_rate':           trace[7],
            'aircraft':
                {k: trace[8].get(k, None)
                    if trace[8] else None
                 for k in aircraft_keys},
            'source':                  trace[9],
            'geometric_altitude':      trace[10],
            'geometric_vertical_rate': trace[11],
            'indicated_airspeed':      trace[12],
            'roll_angle':              trace[13]}

        out_file.write(json.dumps(rec, sort_keys=True) + '\n')

    return num_recs, out_filename, out_file


def process_file(filename:str, progress, task, verbose:bool):
    num_recs, out_filename, out_file = 0, None, None

    assert '-planes-readsb-prod-0.tar' in filename

    source_date = '20' + filename.split('v20')[-1]\
                                 .split('-')[0]\
                                 .replace('.', '-')

    with tarfile.open(filename, 'r') as tar:
        for member in tar.getmembers():
            if member.name.endswith('.json'):
                f = tar.extractfile(member)

                if f is not None:
                    rec = json.loads(
                              zlib.decompress(f.read(),
                                              16 + zlib.MAX_WBITS))
                    num_recs, out_filename, out_file = \
                        process_records(rec,
                                        num_recs,
                                        out_filename,
                                        out_file,
                                        source_date,
                                        verbose)
                    if progress:
                        progress.update(task, advance=1)

    if out_file:
        out_file.close()

        if out_filename:
            if verbose:
                print('Compressing %s' % out_filename)

            gzip_jsonl(out_filename)


@app.command()
def main(filename:str,
         verbose: bool = True):
    # Get total number of JSON files that will be processed so the
    # progress tracker knows ahead of time.
    num_recs = 0

    # Counting JSON Files in the TAR file
    for member in track(tarfile.open(filename, 'r').getmembers(),
                        'Counting JSON files'):
        if member.name.endswith('.json'):
            num_recs = num_recs + 1

    with Progress() as progress:
        task = \
            progress.add_task('Enriching %s' % filename,
                              total=num_recs)
        process_file(filename, progress, task, verbose)


if __name__ == "__main__":
    app()
