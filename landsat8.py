import os
import urllib
from collections import namedtuple

import pandas as pd
import pycurl
from bs4 import BeautifulSoup

import customIO
import requests


TableContent = namedtuple('TableContent', ['link', 'link_text', 'text'])

lsat8_url = "https://landsat-pds.s3.amazonaws.com/c1/L8/"


def get_download_url(scene, filename):
    path, row = get_pathrow(scene)
    return lsat8_url + f"{path:03d}/{row:03d}/{scene}/{filename}"


def download_file(url, filepath, replace=False):
    part_file = f'{filepath}.part'
    c = pycurl.Curl()
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.NOPROGRESS, 0)
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


def get_scenes(path, row, latest=False, scene_str=''):
    if not os.path.exists('./data/index.gz'):
        download_index()
    df = pd.read_csv('./data/index.gz')
    df_filter = df[(df.row == row) & (df.path == path)]
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


def get_band_filename(scene, band):
    data_dir = get_data_dir(scene)
    band_fn = os.path.join(data_dir, f'B{band.value}-{band.name}.TIF')
    return band_fn


def download_band(scene_str, band):
    outfile = get_band_filename(scene_str, band)
    band_url = get_download_url(scene_str, f'{scene_str}_B{band.value}.TIF')
    download_file(band_url, outfile)


def download_scene_file(scene_str, filename):
    data_dir = get_data_dir(scene_str)
    file_url = get_download_url(scene_str, filename)
    outfile = os.path.join(data_dir, filename.split('_')[-1])
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


def get_yn(prompt):
    while True:
        choice = customIO._input(f'{prompt} (y/n):', str).lower()
        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        print(f"Given response '{choice}' is not 'y' or 'n'.")


def choose_from_list(input_list):
    if len(input_list) == 0:
        return None, None
    print('\nAvailable Options:')
    for i, l in enumerate(input_list):
        print(f'{i}-{l}')
    choice = customIO._input(f'your choice(0-{i})', int)
    return choice, input_list[choice]


def choose_scene():
    while True:
        yes_str = get_yn('Do you have Scene string representation?')
        if yes_str:
            scene_str = customIO._input('Enter Scene string representation',
                                        str)
            path, row = get_pathrow(scene_str)
            scene = get_scenes(path, row, scene_str=scene_str)
        else:
            path = customIO._input('Enter path:', int)
            row = customIO._input('Enter row:', int)
            yes_recent = get_yn('Do you want most recent data?')
            scene = get_scenes(path, row, yes_recent)
            if not yes_recent:
                j, s = choose_from_list(list(scene.productId))
                scene = scene.iloc[j].squeeze()
        print('You selected:')
        for i, c in scene.iteritems():
            print(f'{i:15s}\t:{c}')
        confirm = get_yn('Confirm selection?')
        if confirm:
            return scene.productId
        elif not get_yn('Do you want to search again?'):
            return None


def choose_file(scene):
    files = get_available_files(scene)
    desc = [f.text for f in files]
    i, f = choose_from_list(desc)
    return files[i]


def main():
    scene = choose_scene()
    f = choose_file(scene)
    download_scene_file(scene, f.link_text)


if __name__ == '__main__':
    main()
