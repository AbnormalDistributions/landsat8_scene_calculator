#!/usr/bin/env python
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
import sys
import time
import argparse
from enum import Enum

import numpy as np
import rasterio
import requests

import landsat8
import customIO
from landsat8 import Bands


#note that the multiple selection only works if ImageType enum has less than 9 members
class ImageType(Enum):
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


# Define image names and bands required for calculations
images_list = [
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


def get_image_filename(scene, image):
    return os.path.join(
        landsat8.get_data_dir(scene),
        f'{"S" if image.value>1 else "I"}{image.value}-{image.name}.TIF')


def print_hz_line():
    """prints a horizontal line in console
    """
    cols, _ = os.get_terminal_size()
    print('-' * cols)


def get_images():
    indices, _ = customIO.choose_from_list(
        'Select a calculation type to output',
        [f'({image[0]}) - {image[1]}' for image in images_list],
        multiple=True)
    print_hz_line()
    sels = [ImageType(i) for i in indices]
    print(f'ImageType Selected: {[s.name for s in sels]}')
    print_hz_line()
    return sels


def generate_images(scene, images):
    t1 = time.time()
    for img in images:
        print(f'Generating {images_list[img.value][1]} TIFF.')
        print(f'Bands required: {[b.name for b in images_list[img.value][2]]}')
        make_bands(scene, img)
        print_hz_line()
    t2 = time.time()
    print(f'Overall process completed in {t2 - t1:.3f} seconds')


def check_bands_exist(scene, bands_list):
    """function to see if files have been files are present on disk and
save them to disk if not present

    :param bands_list: list of bands to check
    :type bands_list: list of .Bands enum

    """

    for band in bands_list:
        band_file = landsat8.get_band_filename(scene, band)
        if not os.path.exists(band_file):
            print(f'{band.name} band not found in local directory.')
            landsat8.download_band(scene, band)
        else:
            print(f'{band.name} band loaded from local directory.')


def get_bands(scene, band_list):
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
        input_file = landsat8.get_band_filename(scene, band)
        # Open the files and append to 'temp' list
        with rasterio.open(input_file) as open_file:
            meta = open_file.meta
            open_file32 = open_file.read(1).astype('float32')
            # Set 0's to NaN in the arrays tro allow for division
            open_file32[open_file32 == 0] = np.nan
            temp_list.append(open_file32)
    return temp_list, meta


def stack_tiffs(bands_list, scene, filename):
    """stacks the tiffs on band list to make a merged tiff

    :param bands_list: list of bands to merge
    :type bands_list: Bands enum
    :param filename: name of the file to save the merged tiff
    :type filename: string

    """

    file_list = [
        landsat8.get_band_filename(scene, band) for band in bands_list
    ]
    # only metadata of first file is read to copy to the merge tiff
    with rasterio.open(file_list[0]) as src0:
        meta = src0.meta
    meta.update(count=len(file_list))

    with rasterio.open(filename, 'w', **meta) as dst:
        for i, layer in enumerate(file_list, start=1):
            with rasterio.open(layer) as src1:
                dst.write_band(i, src1.read(1))
    print(f'Successfully created: {filename}')


def make_bands(scene_name, image):
    """makes bands for the image and saves it.

    :param image: image to be created/calculated
    :type image: ImageType enum

    """

    bands_list = images_list[image.value][2]
    check_bands_exist(scene_name, bands_list)

    #enum images has merger images except for 0 and 1
    if image.value > 1:
        stack_tiffs(bands_list, scene_name,
                    get_image_filename(scene_name, image))
        return

    bands, meta = get_bands(scene_name, bands_list)
    meta.update(dtype='float32')
    print(f'Calculating {image.name} image from bands.')
    if image == ImageType.NDVI:
        band = calc_ndvi_bands(bands)
    elif image == ImageType.SAVI:
        band = calc_savi_bands(bands)
    export_tif(get_image_filename(scene_name, image), band, meta)


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


def run_interactive(scene=None, images=None):
    """main interactive interface
    """
    if scene == None:
        print('Select the scene with which you would like to work:')
        scene = landsat8.choose_scene()
        print_hz_line()
    if images == None:
        images = get_images()
    generate_images(scene, images)
    return 0


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
    aps.add_argument('--image',
                     nargs='+',
                     choices=[i.name for i in ImageType],
                     help='acronym for Image file to generate')
    aps.add_argument('--scene', help='String Representation of Scene')

    ARGS = aps.parse_args(sys.argv[1:])
    customIO.AUTO_INPUT = ARGS.auto
    images = None
    if ARGS.auto or ARGS.interactive:
        sys.exit(run_interactive())
    if ARGS.image:
        images = [ImageType[img] for img in ARGS.image]
    if ARGS.scene:
        if not landsat8.verify_scene_str(ARGS.scene):
            raise SystemExit('Entered scene is not available.')

    run_interactive(scene=ARGS.scene, images=images)


if __name__ == '__main__':
    main()
