import argparse
import os
import re
import sys
import urllib
from collections import namedtuple
from enum import Enum

import pandas as pd
import pycurl
from bs4 import BeautifulSoup

import customIO
import requests


TableContent = namedtuple('TableContent', ['link', 'link_text', 'text'])

lsat8_url = "https://landsat-pds.s3.amazonaws.com/c1/L8/"


class Bands(Enum):
    AEROSOL = 1
    BLUE = 2
    GREEN = 3
    RED = 4
    NEAR_IR = 5
    SHORT_IR1 = 6
    SHORT_IR2 = 7
    PANCROMATIC = 8
    CIRRUS = 9
    LONG_IR1 = 10
    LONG_IR2 = 11


class Downloader:
    curls = []
    processes = []
    # TODO: multicurl downloader


def index_df():
    if not os.path.exists('./data/index.gz'):
        download_index()

    print('Searching Database...')
    df = pd.read_csv('./data/index.gz')
    return df


def get_download_url(scene, filename):
    path, row = get_pathrow(scene)
    return lsat8_url + f"{path:03d}/{row:03d}/{scene}/{filename}"


def download_file(url,
                  filepath,
                  replace=customIO.REPLACE_DOWNLOADED,
                  mcurl=None):
    part_file = f'{filepath}.part'
    c = pycurl.Curl()
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.NOPROGRESS, 0)
    if os.path.exists(filepath) and replace == False:
        print('File already downloaded, skipping.')
        return
    if os.path.exists(part_file) and replace == False:
        print('Previously Downloaded part found.')
        wmode = 'ab'
        c.setopt(pycurl.RESUME_FROM, os.path.getsize(part_file))
    else:
        wmode = 'wb'
    try:
        with open(part_file, wmode) as writer:
            c.setopt(pycurl.WRITEDATA, writer)
            c.perform()
            c.close()
    except (KeyboardInterrupt, pycurl.error) as e:
        c.close()
        raise SystemExit(f"Download Failed {e}")

    os.rename(part_file, filepath)


def download_index():
    download_file(urllib.parse.urljoin(lsat8_url, "scene_list.gz"),
                  './data/index.gz')


def verify_scene_str(scene):
    df = index_df()
    s = df[df.productId == scene].squeeze()
    return not s.empty


def get_scenes(path, row, latest=False, scene_str=''):
    df = index_df()
    df_filter = df[(df.row == row)
                   & (df.path == path)].sort_values('acquisitionDate')
    if latest:
        return df_filter.iloc[-1].squeeze()
    if scene_str:
        return df_filter[df_filter.productId == scene_str].squeeze()
    return df_filter


def get_data_dir(scene_str):
    path, row = get_pathrow(scene_str)
    data_dir = f'./data/{path:03d}{row:03d}/{scene_str}/'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_band_filename(scene, band, filetype='TIF'):
    data_dir = get_data_dir(scene)
    band_fn = os.path.join(data_dir, f'B{band.value}-{band.name}.{filetype}')
    return band_fn


def download_band(scene_str, band, filetype='TIF'):
    outfile = get_band_filename(scene_str, band, filetype)
    band_url = get_download_url(scene_str,
                                f'{scene_str}_B{band.value}.{filetype}')
    download_file(band_url, outfile)


def download_bands(scene_str, bands_list, filetype='TIF'):
    mcrl = pycurl.CurlMulti()
    # TODO: multicurl download multiple bands


def download_scene_file(scene_str, filename):
    data_dir = get_data_dir(scene_str)
    file_url = get_download_url(scene_str, filename)
    m = re.match(r'B([0-9]+)([._].*)', filename.split('_')[-1])
    if m:
        band_no = int(m.group(1))
        custom_filename = f'B{band_no}-{Bands(band_no).name}{m.group(2)}'
    else:
        custom_filename = filename.split('_')[-1]
    outfile = os.path.join(data_dir, custom_filename)
    download_file(file_url, outfile)


def get_pathrow(scene_str):
    pathrow = scene_str.split('_')[2]
    path = int(pathrow[:3])
    row = int(pathrow[3:])
    return path, row


def get_soup(url):
    r = requests.get(url)
    return BeautifulSoup(r.text, 'html.parser')


def get_index_html_url(url):
    return urllib.parse.urljoin(url, 'index.html')


def html_list(url):
    soup = get_soup(url)
    elements = soup.find_all('li')
    contents = [
        TableContent(urllib.parse.urljoin(url, e.a['href']), e.a.text, e.text)
        for e in elements
    ]
    return contents


def get_available_files(scene):
    path, row = get_pathrow(scene)
    url = lsat8_url + f"{path:03d}/{row:03d}/{scene}/index.html"
    files = html_list(url)
    return files


def confirm_scene(scene_obj):
    print('You selected:')
    for i, c in scene_obj.iteritems():
        print(f'{i:15s}\t:{c}')
    confirm = customIO.get_yn('Confirm selection?')
    if confirm:
        return True, scene_obj.productId
    elif customIO.get_yn('Do you want to search again?'):
        return False, None
    else:
        return True, None


def choose_scene_pathrow(path, row):
    yes_recent = customIO.get_yn('Do you want most recent data?')
    scene = get_scenes(path, row, yes_recent)
    if not yes_recent:
        options = [
            f'{r.productId} (CC:{r.cloudCover:2.2f}%)'
            for i, r in scene.iterrows()
        ]
        j, s = customIO.choose_from_list(
            'Choose the scene you want to work on', options)
        scene = scene.iloc[j].squeeze()
    success, scene_str = confirm_scene(scene)
    if success:
        return scene_str
    else:
        raise SystemExit(0)


def choose_scene():
    while True:
        yes_str = customIO.get_yn('Do you have Scene string representation?')
        if yes_str:
            scene_str = customIO._input('Enter Scene string representation',
                                        str)
            if verify_scene_str(scene_str):
                return scene_str
            print('Given String representation is not in database.')
            if customIO.get_yn('Update Database?'):
                download_index()
            continue
        else:
            path = customIO._input('Enter path:', int)
            row = customIO._input('Enter row:', int)
            scene_str = choose_scene_pathrow(path, row)
            return scene_str


def choose_file(scene):
    files = get_available_files(scene)
    desc = [f.text for f in files]
    indices, _ = customIO.choose_from_list('Choose the files to download:',
                                           desc,
                                           multiple=True)
    return [files[i] for i in indices]


def run_interactive(scene):
    files = choose_file(scene)
    for f in files:
        download_scene_file(scene, f.link_text)


def main():
    aps = argparse.ArgumentParser()
    aps.add_argument('-i',
                     '--interactive',
                     help='Start Interactive Session',
                     action='store_true')
    aps.add_argument('-a',
                     '--auto',
                     help='Repeate the actions of last Interactive Session',
                     action='store_true')
    aps.add_argument('-r',
                     '--replace',
                     help='Replace the previously downloaded files',
                     action='store_true')
    aps.add_argument('--scene', help='String Representation of Scene')
    aps.add_argument('--bands-no',
                     nargs='+',
                     type=int,
                     choices=[b.value for b in Bands],
                     help='Number of bands to download')
    aps.add_argument('--bands',
                     nargs='+',
                     choices=[b.name for b in Bands],
                     help='Name of bands to download')
    aps.add_argument('--file-type',
                     help='File extension to download',
                     default='TIF')
    aps.add_argument('--wrs-path', help='WRS path of scene location', type=int)
    aps.add_argument('--wrs-row', help='WRS row of scene location', type=int)

    ARGS = aps.parse_args(sys.argv[1:])
    customIO.AUTO_INPUT = ARGS.auto
    customIO.REPLACE_DOWNLOADED = ARGS.replace
    bands = []
    if ARGS.auto or ARGS.interactive:
        sys.exit(run_interactive())
    if ARGS.bands:
        bands += [Bands[b] for b in ARGS.bands]
    if ARGS.bands_no:
        bands += [Bands(bn) for bn in ARGS.bands_no]

    if ARGS.wrs_path and ARGS.wrs_row:
        scene = choose_scene_pathrow(ARGS.wrs_path, ARGS.wrs_row)
    elif ARGS.scene:
        if not verify_scene_str(ARGS.scene):
            raise SystemExit('Entered scene is not available.')
        scene = ARGS.scene
    else:
        scene = choose_scene()
    if bands:
        for b in bands:
            download_band(scene, b, ARGS.file_type)
        sys.exit(0)
    run_interactive(scene)


if __name__ == '__main__':
    main()
