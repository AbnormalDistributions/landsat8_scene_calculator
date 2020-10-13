'''
Date: 2020/10/10
Initial Author: James Steele Howard
Contributors: Gaurav Atreya

This script creates GeoTIFF files of the following:
- Normalized Difference Vegetation Index
- Soil Adjusted Vegetation Index
- Visible Spectrum (Natural Color)
- Short Wave Infrared
- Agriculture
- Bathymetric
'''
import os
from enum import Enum
import time
import numpy as np
import rasterio
import requests
import sys

#TODO: make this interactive, maybe there are some api to get the url.
url_base = 'https://landsat-pds.s3.amazonaws.com/c1/L8/046/028/LC08_L1TP_046028_20200908_20200918_01_T1/LC08_L1TP_046028_20200908_20200918_01_T1_B'


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


class Scenes(Enum):
    NDVI = 0
    SAVI = 1
    RGB = 2
    NIR = 3
    SWI = 4
    AGR = 5
    GEO = 6
    BMC = 7


def calc_ndvi_bands(bands):
    """calculates the ndv index band 

    :param bands: list of bands
    :type bands: np.darray
    :returns: single band of sav index
    :rtype: np.darray

    """
    return np.array((bands[1] - bands[0]) / (bands[1] + bands[0]))


def calc_savi_bands(bands):
    """calculates the sav index band

    :param bands: list of bands
    :type bands: np.darray
    :returns: single band of sav index
    :rtype: np.darray

    """

    return np.array(
        (((bands[1] - bands[0]) / (bands[1] + bands[0] + 0.5)) * 1.5))


# Define scene names and bands required for calculations
scenes_list = [
    # short name, full name, bands required for calculation, calculation function, band count
    ('NDVI', 'Normalized Difference Vegetation Index',
     [Bands.RED, Bands.NEAR_IR]),
    ('SAVI', 'Soil Adjusted Vegetation Index', [Bands.RED, Bands.NEAR_IR]),
    ('RGB', 'Visible Spectrum (Natural Color)',
     [Bands.RED, Bands.GREEN, Bands.BLUE]),
    ('NIR', 'Near Infrared Composite (Color Infrared)',
     [Bands.NEAR_IR, Bands.RED, Bands.GREEN]),
    ('SWI', 'Short Wave Infrared',
     [Bands.SHORT_IR2, Bands.SHORT_IR1, Bands.RED]),
    ('AGR', 'Agriculture', [Bands.SHORT_IR1, Bands.NEAR_IR, Bands.BLUE]),
    ('GEO', 'Geology', [Bands.SHORT_IR2, Bands.SHORT_IR1, Bands.BLUE]),
    ('BMC', 'Bathymetric', [Bands.RED, Bands.GREEN, Bands.AEROSOL])
]


def get_data_dir():
    """get the data directory where TIFFs are stored.

    :returns: full path to data directory
    :rtype: string

    """
    main_dir = os.getcwd()
    data_dir = os.path.join(main_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print('data_dir did not exist. New data directory created.')
    return (data_dir)


def get_band_file(band):
    return os.path.join(get_data_dir(), f'{band.value}-{band.name}.TIF')


def get_scene_file(scene):
    return os.path.join(get_data_dir(), f'{scene.name}.TIF')


def print_hz_line():
    """prints a horizontal line in console
    """
    cols = 50
    print('-' * cols)


def main():
    """main interactive interface
    """
    print_hz_line()
    print(
        'Select a calculation type (input more than on number to select multiple):'
    )
    for i, scene in enumerate(scenes_list):
        print(f'{i + 1}: ({scene[0]}) - {scene[1]}')
    print('\n0: *Exit*')
    print_hz_line()
    # Take Input and process selection
    selection = input('>')
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
        make_bands(Scenes(s))
        print_hz_line()
    t2 = time.time()
    print(f'Overall process completed in {t2 - t1:.3f} seconds')


def download_band(band):
    """function for obtaining file from internet resource and save it to
disk

    :param band: band to download to disk
    :type band: .Bands enum

    """
    output_file = get_band_file(band)
    # Set TIF file URL to be requested
    band_url = f'{url_base}{band.value}.TIF'
    # Request file
    print(f'Getting {band.name} from web.')
    save_file_from_web(band_url, output_file)


def check_bands_exist(bands_list):
    """function to see if files have been files are present on disk and
save them to disk if not present

    :param bands_list: list of bands to check
    :type bands_list: list of .Bands enum

    """

    for band in bands_list:
        band_file = get_band_file(band)
        if not os.path.exists(band_file):
            print(f'{band.name} band not found in local directory.')
            download_band(band)
        else:
            print(f'{band.name} band loaded from local directory.')


def save_file_from_web(url, filename):
    """function for retrieving files from URL and writing them to disk

    :param url: url of the file on web
    :type url: string
    :param filename: name of the file to save on disk
    :type filename: string
    :returns: True if success False if not
    :rtype: bool
    """
    r = requests.get(url, stream=True, allow_redirects=True)
    if r.status_code != 200:
        print('Connection Error.')
        return False

    size = r.headers.get('Content-Length')
    if size == None:
        print('Download file size unknown. Downloading...')
        with open(filename, 'wb') as writer:
            writer.write(r.content)
        print('Download Complete)')
        return True
    print(f'Downloading file...')
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
    except (KeyboardInterrupt, requests.exceptions.ChunkedEncodingError) as e:
        print(f'Download Interupted.{e} \nTry again...')
        if os.path.exists(filename):
            os.remove(filename)
        sys.exit(1)
    print('\nDownload Completed')
    return True


def get_bands(band_list):
    """function for creating and return a list containing all band data

    :param band_list: list of bands to load
    :type band_list: list of Bands enum
    :returns: list of bands and metadata
    :rtype: tuple (bands_list, metadata)

    """

    # Read in the TIF files from disk.
    ## Initialize temp list
    temp_list = []
    for band in band_list:
        input_file = get_band_file(band)
        # Open the files and append to 'temp' list
        with rasterio.open(input_file) as open_file:
            meta = open_file.meta
            open_file32 = open_file.read(1).astype('float32')
            # Set 0's to NaN in the arrays tro allow for division
            open_file32[open_file32 == 0] = np.nan
            temp_list.append(open_file32)
    return temp_list, meta


def stack_tiffs(bands_list, filename):
    """stacks the tiffs on band list to make a merged tiff

    :param bands_list: list of bands to merge 
    :type bands_list: Bands enum
    :param filename: name of the file to save the merged tiff
    :type filename: string

    """

    file_list = [get_band_file(band) for band in bands_list]
    # only metadata of first file is read to copy to the merge tiff
    with rasterio.open(file_list[0]) as src0:
        meta = src0.meta
    meta.update(count=len(file_list))

    with rasterio.open(filename, 'w', **meta) as dst:
        for i, layer in enumerate(file_list, start=1):
            with rasterio.open(layer) as src1:
                dst.write_band(i, src1.read(1))
    print(f'Successfully created: {filename}')


def make_bands(scene):
    """makes bands for the scene and saves it.

    :param scene: scene to be created/calculated
    :type scene: Scenes enum

    """

    bands_list = scenes_list[scene.value][2]
    check_bands_exist(bands_list)

    #enum scenes has merger scenes except for 0 and 1
    if scene.value > 1:
        stack_tiffs(bands_list, get_scene_file(scene))
        return

    bands, meta = get_bands(bands_list)
    meta.update(dtype='float32')
    print(f'Calculating {scene.name} scene from bands.')
    if scene == Scenes.NDVI:
        band = calc_ndvi_bands(bands)
    elif scene == Scenes.SAVI:
        band = calc_savi_bands(bands)
    export_tif(get_scene_file(scene), band, meta)


def export_tif(file_name, band, meta):
    """function to export a band to tiff file.

    :param file_name: filename to be saved
    :type file_name: string
    :param band: band data to be saved
    :type band: numpy.darray
    :param meta: metadata of the file
    :type meta: python Dictionary

    """

    with rasterio.open(file_name, 'w', **meta) as out:
        out.write_band(1, band)
    print(f'Successfully created: {file_name}')


if __name__ == '__main__':
    main()