import os
import urllib
from collections import namedtuple

import pandas as pd
import pycurl
from bs4 import BeautifulSoup

import requests


TableContent = namedtuple('TableContent', ['link', 'link_text', 'text'])

lsat8_url = "https://landsat-pds.s3.amazonaws.com/c1/L8/"


def get_download_url(scene, filename):
    path, row = get_pathrow(scene)
    return lsat8_url + f"{path:03d}/{row:03d}/{scene}/{filename}"


def download_file(url, filepath):
    with open(filepath, 'wb') as writer:
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.WRITEDATA, writer)
        c.setopt(pycurl.NOPROGRESS, 0)
        try:
            c.perform()
        except pycurl.error as e:
            print("Download Failed...")
            raise pycurl.error(e)
        c.close()


def download_index():
    download_file(urllib.parse.urljoin(lsat8_url, "scene_list.gz"),
                  './data/index.gz')


def get_scenes(path, row, latest=False, scene_str=''):
    if not os.path.exists('./data/index.gz'):
        download_index()
    df = pd.read_csv('./data/index.gz')
    df_filter = df[df.row == row][df.path == path]
    if latest:
        return df_filter.iloc[-1].squeeze()
    if scene_str:
        return df_filter[df_filter.productId==scene_str].squeeze()
    return df_filter


def download_band(scene_str, band):
    path, row = get_pathrow(scene_str)
    data_dir = f'./data/{path:03d}{row:03d}/{scene_str}/'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir,exist_ok=True)
    band_fn = os.path.join(data_dir, f'{band.name}.TIF')
    band_url = get_download_url(scene_str, f'{scene_str}_B{band.value}.TIF')
    download_file(band_url, band_fn)


def download_scene_file(scene_str, filename):
    path, row = get_pathrow(scene_str)
    data_dir = f'./data/{path:03d}{row:03d}/{scene_str}/'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir,exist_ok=True)
    outfile = os.path.join(data_dir, filename)
    file_url = get_download_url(scene_str, filename)
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


# def show_available_scenes(wrs_path, wrs_row):
#     df = get_scenes_url(wrs_path, wrs_row)
#     for i, r in df.iterrows():
#         print(f'{i}\t:{r.elementId}')
#     return list(r.download_url)


def get_available_files(scene):
    path, row = get_pathrow(scene)
    url = lsat8_url + f"{path:03d}/{row:03d}/{scene}/index.html"
    files = html_list(url)
    return files

def get_yn(prompt):
    while True:
        choice = input(f'{prompt} (y/n):<y>').lower()
        if choice == 'y' or choice =='':
            return True
        elif choice == 'n':
            return False
        print(f"Given response '{choice}' is not 'y' or 'n'.")

def choose_from_list(input_list):
    if len(input_list)==0:
        return None,None
    for i,l in enumerate(input_list):
        print(f'{i}-{l}')
    choice = int(input(f'Enter your choice(0-{i}):'))
    return choice,input_list[choice]


def choose_scene():
    while True:
        yes_str = get_yn('Do you have Scene string representation?')
        if yes_str:
            scene_str = input('Enter the string representation:')
            path, row = get_pathrow(scene_str)
            scene = get_scenes(path, row, scene_str = scene_str)
        else:
            path = int(input('Enter path:'))
            row = int(input('Enter row:'))
            yes_recent = get_yn('Do you want most recent data?')
            scene = get_scenes(path,row,yes_recent)
            if not yes_recent:
                j,s = choose_from_list(list(scene.productId))
                scene = scene.iloc[j].squeeze()
        print('You selected:')
        for i,c in scene.iteritems():
            print(f'{i:15s}\t:{c}')
        confirm = get_yn('Confirm selection?')
        if confirm:
            return scene.productId
        elif not get_yn('Do you want to search again?'):
            return None

def choose_file(scene):
    files = get_available_files(scene)
    desc = [f.text for f in files]
    i,f = choose_from_list(desc)
    return files[i]

def main():
    scene = choose_scene()
    f = choose_file(scene)
    f.link_text
    download_scene_file(scene, f.link_text)

if __name__ == '__main__':
    main()

