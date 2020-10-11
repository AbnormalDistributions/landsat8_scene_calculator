# Date: 2020/10/10
# Initial Author: James Steele Howard
# Contributors: Gaurav Atreya
# This script creates NDVIs, SAVIs, RBG, and NIR images using Landsat8 imagery.

import os
from enum import Enum
import time
import numpy as np
import rasterio
import requests

url_base = 'https://landsat-pds.s3.amazonaws.com/c1/L8/046/028/LC08_L1TP_046028_20200908_20200918_01_T1/LC08_L1TP_046028_20200908_20200918_01_T1_B'

# Create enumeration for bands
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

# Create enumeration for scene type
class Scenes(Enum):
    NDVI = 0
    SAVI = 1
    RGB = 2
    NIR = 3
    SWI = 4
    AG = 5
    GEO = 6
    BAT = 7

def calc_ndvi_bands(bands):
    return np.array((bands[1] - bands[0]) / (bands[1] + bands[0]))

def calc_savi_bands(bands):
    return np.array(((bands[1] - bands[0]) / (bands[1] + bands[0] + 0.5)) * 1.5)

def combine_bands(bands):
    return np.array(bands)

# Define scene names and bands required for calculations
scenes_list = [
    # short name, full name, bands required for calculation, calculation function, band count
    ('NDVI', 'Normalized Difference Vegetation Index', [Bands.RED, Bands.NEAR_IR],
                                                calc_ndvi_bands, 1),
    ('SAVI', 'Soil Adjusted Vegetation Index', [Bands.RED, Bands.NEAR_IR], calc_savi_bands, 1),
    ('RGB', 'Visible Spectrum (Natural Color)', [Bands.RED, Bands.GREEN, Bands.BLUE],
                                                combine_bands, 3),
    ('NIR', 'Near Infrared Composite (Color Infrared)', [Bands.NEAR_IR, Bands.RED, Bands.GREEN],
                                                combine_bands, 3),
    ('SWI', 'Short Wave Infrared', [Bands.SHORT_IR2, Bands.SHORT_IR1, Bands.RED],
                                                combine_bands, 3),
    ('AG', 'Agriculture', [Bands.SHORT_IR1, Bands.NEAR_IR, Bands.BLUE], combine_bands, 3),
    ('GEO', 'Geology', [Bands.SHORT_IR2, Bands.SHORT_IR1, Bands.BLUE], combine_bands, 3),
    ('BAT', 'Bathymetric', [Bands.RED, Bands.GREEN, Bands.AEROSOL], combine_bands, 3)
    ]

# Define function fo printing horizontal line for menus
def print_hz_line():
    cols = 50
    print('-' * cols)

def main():
    # Display the main menu
    print_hz_line()
    print('Select a calculation type (input more than on number to select multiple):')
    for i, scene in enumerate(scenes_list):
        print(f'{i + 1}: ({scene[0]}) - {scene[1]}')
    print('\n0: *Exit*')
    print_hz_line()
    # Take Input and process selection
    selection =input('>')
    if int(selection) == 0:
        print('Exiting...')
        return
    sels = [int(s) - 1 for s in list(selection.strip())]
    print(f'Scenes Selected: {[scenes_list[s][0] for s in sels]}')
    print_hz_line()
    t1 = time.time()
    for s in sels:
        print(f'Generating {scenes_list[s][1]} TIFF.')
        print(f'Bands required: {[b.name for b in scenes_list[s][2]]}')
        print_hz_line()
        make_bands(Scenes(s))
    t2 = time.time()
    print(f'Overall process completed in {t2 - t1:.3f} seconds')

# Define function for setting creating the data directory if it doesn't exist
def get_data_dir():
    # Set the main directory
    main_dir = os.getcwd()
    # Set and crate data directory if it doesn't exist
    data_dir = os.path.join(main_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print('data_dir did not exist. New data directory created.')
    return (data_dir)

# Define function for obtaining file from internet resource
# and save it to disk
def download_band(band):
    TIF_file_name = f'{band.name}.TIF'
    output_file = os.path.join(get_data_dir(), TIF_file_name)
    # Set TIF file URL to be requested
    band_url = f'{url_base}{band.value}.TIF'
    # Request file
    print(f'Getting {band.name} from web.')
    save_file_from_web(band_url, output_file)

# Define function to see if files have been files are present on disk
# and save them to disk if not present
def check_bands_exist(bands_list):
    for band in bands_list:
        TIF_file_name = f'{band.name}.TIF'
        output_file = os.path.join(get_data_dir(), TIF_file_name)
        if not os.path.exists(output_file):
            print(f'{band.name} band not found locally.')
            download_band(band)
        else:
            print(f'{band.name} band found locally.')

# Define function for retrieving files from URL and writing them to disk
def save_file_from_web(url, filename):
    # Request file
    r = requests.get(url, stream=True, allow_redirects=True)
    # Display error if there is a problem with the connection
    if r.status_code !=200:
        print('Connection Error.')
        return False
    # Save the TIFF to disk
    # Determine content length
    size = r.headers.get('Content-Length')
    # Skip loading animation if no content length not present
    # and write to disk
    if size == None:
        print('Download file size unknown. Downloading...')
        with open(filename, 'wb') as writer:
            writer.write(r.content)
        print('Download Complete)')
        return True
    print(f'Downloading file...')
    # Display loading animation if cont length present
    # and write to disk
    cols = 50
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
        print('Error while downloading. Try again...')
        # Delete the incompletely downloaded file
        if os.path.exists(filename):
            os.remove(filename)
    print('\nDownload Complete')
    return True

# Define function for creating and return a list containing
# all band data
def get_bands(band_list):
    # Read in the TIF files from disk.
    ## Initialize temp list
    temp_list = []
    for band in band_list:
        TIF_file_name = f'{band.name}.TIF'
        input_file = os.path.join(get_data_dir(), TIF_file_name)
        # Open the files and append to 'temp' list
        with rasterio.open(input_file) as open_file:
            meta = open_file.meta
            open_file32 = open_file.read(1).astype('float32')
            # Set 0's to NaN in the arrays tro allow for division
            open_file32[open_file32 == 0] = np.nan
            temp_list.append(open_file32)
    return temp_list, meta

def stack_tiffs(bands_list, filename):
    file_list = [os.path.join(get_data_dir(), f'{band.name}.TIF') for band in bands_list]
    # Read metadata of first file
    with rasterio.open(file_list[0]) as src0:
        meta = src0.meta
    meta.update(count=len(file_list))
    # Read each layer and write it to stack
    with rasterio.open(filename, 'w', **meta) as dst:
        for i, layer in enumerate(file_list, start=1):
            with rasterio.open(layer) as src1:
                dst.write_band(i, src1.read(1))

def make_bands(scene):
    bands_list = scenes_list[scene.value][2]
    check_bands_exist(bands_list)
    if scene.value > 1:
        stack_tiffs(bands_list, os.path.join(get_data_dir(), f'{scene.name}.TIF'))
        return

    bands, meta = get_bands(bands_list)
    meta.update(dtype='float32')
    band_func = scenes_list[scene.value][3]
    print(f'Calculating {scene.name} scene from bands.')
    band = band_func(bands)
    export_tif(f'{scene.name}.TIF', band, meta)

# Define function for exporting TIF files
def export_tif(file_name, band, meta):
    output_file = os.path.join(get_data_dir(), file_name)
    with rasterio.open(output_file, 'w', **meta) as out:
        out.write_band(1, band)
    print(f'**Successfully created {file_name} and saved to data directory.**')
    print_hz_line()

if __name__ == '__main__':
    main()