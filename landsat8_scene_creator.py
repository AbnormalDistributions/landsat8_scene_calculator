# Date: 2020/10/08
# Author: James Steele Howard
# This script creates NDVIs, SAVIs, RBG, and NIR images using Landsat8 imagery.

import os
from enum import Enum

import numpy as np
import rasterio
import requests


# Set the base URL for the scene
#url_base = 'https://landsat-pds.s3.amazonaws.com/c1/L8/046/028/LC08_L1TP_046028_20200908_20200918_01_T1/LC08_L1TP_046028_20200908_20200918_01_T1_B'
url_base = 'https://landsat-pds.s3.amazonaws.com/c1/L8/141/041/LC08_L1TP_141041_20201004_20201004_01_RT/LC08_L1TP_141041_20201004_20201004_01_RT_B'

class Bands(Enum):
    AEROSOL = 1
    BLUE = 2
    GREEN = 3
    RED = 4
    NEAR_IR = 5
    SHORT_IR = 6
    SHORT_IR2 = 7
    PANCROMATIC = 8
    CIRRUS = 9
    LONG_IR = 10
    LONG_IR2 = 11


class Scenes(Enum):
    NDVI = 0
    SAVI = 1
    RGB = 2
    NIR = 3
    SWI = 4
    AG = 5
    GEO = 6
    BAT = 7


def ndvi_bands(bands):
    return np.array([(bands[1] - bands[0]) / (bands[1] + bands[0])])


def savi_bands(bands):
    return np.array([
        ((bands[1] - bands[0]) / (bands[1] + bands[0] + 0.5)) * 1.5
    ])


def combine_bands(bands):
    return np.array(bands)


scenes_list = [
    ('NDVI', 'Normalized Difference Vegetation', [Bands.RED, Bands.NEAR_IR],
     ndvi_bands, 1),
    ('SAVI', 'Soil Adjusted Vegetation Index', [Bands.RED,
                                                Bands.NEAR_IR], savi_bands, 1),
    ('RGB', 'Visible Spectrum', [Bands.RED, Bands.GREEN,
                                 Bands.BLUE], combine_bands, 3),
    ('NIR', 'False Color Infrared', [Bands.NEAR_IR, Bands.RED,
                                     Bands.GREEN], combine_bands, 3),
    ('SWI', 'Short Wave Infrared', [Bands.SHORT_IR2, Bands.SHORT_IR, Bands.RED], combine_bands, 3),
    ('AG', 'Agreculture', [Bands.SHORT_IR, Bands.NEAR_IR, Bands.BLUE], combine_bands, 3),
    ('GEO', 'Geology', [Bands.SHORT_IR2, Bands.SHORT_IR, Bands.BLUE], combine_bands, 3),
    ('BAT', 'Bathymic', [Bands.RED, Bands.GREEN, Bands.AEROSOL], combine_bands, 3),
    
]


def make_bands(scene):
    bands_list = scenes_list[scene.value][2]
    check_bands_exist(bands_list)
    bands, open_file = create_list(bands_list)
    band_func = scenes_list[scene.value][3]
    band_count = scenes_list[scene.value][4]
    print(f'Calculating {scene.name} scene from bands')
    image_data = band_func(bands)
    export_tif(f'{scene.name}.TIF', image_data, open_file, band_count)
    open_file.close()


def print_hz_line():
    cols, _ = os.get_terminal_size()
    print('-' * (cols - 5))


def get_data_dir():
    # Set the main directory
    main_dir = os.getcwd()
    # Set and create data directory if it doesn't exist
    data_dir = os.path.join(main_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print('data_dir did not exist. New data directory created.')
    return data_dir


def save_file_from_web(url, filename):
    r = requests.get(url, stream=True, allow_redirects=True)
    if r.status_code != 200:
        print('Connection Error')
        return False
    size = r.headers.get('Content-Length', None)
    if size == None:
        print('Download file size unknown. Downloading..')
        with open(filename, 'wb') as writer:
            writer.write(r.content)
        print('Download Complete')
        return True
    print(f'Downloading file ...')
    cols, _ = os.get_terminal_size()
    downloaded = 0
    try:
        with open(filename, 'wb') as writer:
            for data in r.iter_content(chunk_size=1024):
                writer.write(data)
                downloaded += 1024
                perc = int(100 * downloaded / int(size))
                char_len = (downloaded) * (cols - 10) / int(size)
                print('#' * int(char_len), f'{perc}%', end='\r')
    except requests.exceptions.ChunkedEncodingError:
        print('Error while downloding, Try again..')
        # delete the incompletely downloaded file.
        if os.path.exists(filename):
            os.remove(filename)

    print('\nDownload Complete')
    return True


# Define main function that gets user input
def main():
    print_hz_line()
    print('Select a calculation scene (type more than one number to select multiple):')
    for i, scene in enumerate(scenes_list):
        print(f'{i+1}) {scene[1]} ({scene[0]})')
    print('\n0) *Exit*')
    print_hz_line()
    # take input
    selection = input(">")
    if int(selection) == 0:
        print('Existing')
        return
    sels = [int(s)-1 for s in list(selection.strip())]
    print(f'Scenes Selected:{[scenes_list[s][0] for s in sels]}')
    print_hz_line()
    for s in sels:
        print(f'Generating {scenes_list[s][1]} tiff.')
        print(f'Bands required: {[b.name for b in scenes_list[s][2]]}')
        print_hz_line()
        make_bands(Scenes(s))


# Define function for obtaining files from internet resource
# and save them to disk
def check_bands_exist(bands_list):
    for band in bands_list:
        TIF_file_name = f'{band.name}.TIF'
        output_file = os.path.join(get_data_dir(), TIF_file_name)
        if not os.path.exists(output_file):
            print(f'locally {band.name} band file not found.')
            download_band(band)


def download_band(band):
    TIF_file_name = f'{band.name}.TIF'
    output_file = os.path.join(get_data_dir(), TIF_file_name)
    # Set TIF file URL to be requested
    band_url = f'{url_base}{band.value}.TIF'
    # Request file
    print(f'Getting {band.name} band from web.')
    save_file_from_web(band_url, output_file)


# Define function for creating and return a list containing
# all band data
def create_list(band_list):
    # Read in the TIF files from disk.
    ## Initialize temp list
    temp_list = []
    counter = 0
    for band in band_list:
        TIF_file_name = f'{band.name}.TIF'
        # Set location for file to be imported
        input_file = os.path.join(get_data_dir(), TIF_file_name)
        # Open the files and append to 'temp' list
        open_file = rasterio.open(input_file)
        # Set values to floats to be able to be used in numpy
        open_file32 = open_file.read(1).astype('float32')
        # Set 0's to NaN in the arrays tro allow for division
        open_file32[open_file32 == 0] = np.nan
        # Append raw data to temporary list
        temp_list.append(open_file32)
    return temp_list, open_file


# Define function for exporting TIF files
def export_tif(file_name, image_data, open_file, band_count):
    ## Set output file
    output_file = os.path.join(get_data_dir(), file_name)
    ## Write the file to disk
    image = rasterio.open(output_file,
                          'w',
                          driver='Gtiff',
                          height=open_file.height,
                          width=open_file.height,
                          count=band_count,
                          crs=open_file.crs,
                          transform=open_file.transform,
                          dtype='float32')
    index = 1
    for array in image_data:
        image.write(array, index)
        index += 1
    image.close()
    print(f'**Successfully created {file_name} and saved to data directory.**')
    print_hz_line()


if __name__ == '__main__':
    main()
