#! python

"""
Date: 2020/10/12
Initial Author: James Steele Howard
Contributors: Gaurav Atreya, and_viceversa

This script creates GeoTIFF files of the following:
- Normalized Difference Vegetation Index
- Soil Adjusted Vegetation Index
- Visible Spectrum
- Near Infrared Composite
- Short Wave Infrared
- Agriculture
- Geology
- Bathymetric
"""

import argparse
import os
import sys
import time

import numpy as np
import rasterio
import requests

bands = {
    'AEROSOL': 1,
    'BLUE': 2,
    'GREEN': 3,
    'RED': 4,
    'NEAR_IR': 5,
    'SHORT_IR1': 6,
    'SHORT_IR2': 7,
    'PANCHROMATIC': 8,
    'CIRRUS': 9,
    'LONG_IR1': 10,
    'LONG_IR2': 11
}

# short name, full name, bands required for calculation
scenes_list = {
    1: ('NDVI', 'Normalized Difference Vegetation Index', ['RED', 'NEAR_IR']),
    2: ('SAVI', 'Soil Adjusted Vegetation Index', ['RED', 'NEAR_IR']),
    3: ('RGB', 'Visible Spectrum (Natural Color)', ['RED', 'GREEN', 'BLUE']),
    4: ('NIR', 'Near Infrared Composite (Color Infrared)', ['NEAR_IR', 'RED', 'GREEN']),
    5: ('SWI', 'Short Wave Infrared', ['SHORT_IR2', 'SHORT_IR1', 'RED']),
    6: ('AGR', 'Agriculture', ['SHORT_IR1', 'NEAR_IR', 'BLUE']),
    7: ('GEO', 'Geology', ['SHORT_IR2', 'SHORT_IR1', 'BLUE']),
    8: ('BMC', 'Bathymetric', ['RED', 'GREEN', 'AEROSOL'])
}


class L8CALC:

    def __init__(self, url, output_scenes, verbose=False):
        """
        :param url: str from user input. Must be valid AWS Landsat 8 scene
        :param output_scenes: list of int corresponding to scenes_list [1,2,3 ...]
        :param verbose: bool to determine print output
        """
        global bands
        global scenes_list

        self.start_time = time.time()
        self.scene_url = url
        self.output_scenes = output_scenes
        self.verbose_output = verbose

        # simple check to accept full URLs
        if url.lower().endswith('.tif'):
            self.url_base = url[:-5].strip()
        else:
            self.url_base = url.strip()

        self.output_dir = os.path.join(os.getcwd(), f'ls8_{self.url_base.split("_")[2]}_{self.url_base.split("_")[3]}')

        # create output directory
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            self.verbose(f'{self.output_dir} did not exist. New data directory created.')

        # group required bands
        self.required_bands = set([band for s in self.output_scenes for band in scenes_list[s][2]])

        # download required bands if necessary
        self.get_bands()

        # write scenes
        [self.write_scenes(scenes_list[scene_num]) for scene_num in self.output_scenes]

        self.verbose(f'Overall process completed in {time.time() - self.start_time:.3f} seconds')

    def get_bands(self):
        """If required bands exist, skip. Else, download."""

        for band in self.required_bands:
            band_file = self.get_band_filename(band)
            if not os.path.exists(band_file):
                self.verbose(f'{band} band not found in local directory.')
                self.save_file_from_web(band, band_file)
            else:
                self.verbose(f'{band} band loaded from local directory.')

    def save_file_from_web(self, band, band_file):
        """retrieve files from URL and write them to disk"""

        self.verbose(f'\tDownloading {band} band...')

        band_url = f'{self.url_base}{bands[band]}.TIF'

        try:
            r = requests.get(band_url, stream=True, allow_redirects=True)
            if r.status_code != 200:
                raise ConnectionError
            size = r.headers.get('Content-Length')
            if size is None:
                self.verbose('\tDownload file size unknown. Downloading...')
                with open(band_file, 'wb') as writer:
                    writer.write(r.content)
                self.verbose(f'\t{band} Download Complete')
                return True
        except ConnectionError as e:
            self.verbose(f'\tConnection Error on {band}. Unable to download. Quitting...')
            quit()

        cols = 50
        downloaded = 0
        try:
            with open(band_file, 'wb') as writer:
                for data in r.iter_content(chunk_size=1024):
                    writer.write(data)
                    downloaded += 1024
                    char_len = downloaded * (cols - 10) / int(size)
                    self.verbose('#' * int(char_len), end='\r')
                self.verbose(f'\t{band} Download Complete')
                return True
        except (KeyboardInterrupt, requests.exceptions.ChunkedEncodingError) as e:
            self.verbose(f'Download Interrupted. {e} \nTry again...')
            if os.path.exists(band_file):
                os.remove(band_file)
            sys.exit(1)

    def write_scenes(self, scene_info):
        if scene_info[0] not in ['NDVI', 'SDVI']:
            self.stack_tiffs(scene_info)
            return
        else:
            raster_list, meta = self.get_rasters(scene_info)
            meta.update(dtype='float32')
            self.verbose(f'Calculating {scene_info[0]} scene from bands.')
            if scene_info[0] == 'NDVI':
                band = self.calc_ndvi_bands(raster_list)
            elif scene_info[0] == 'SDVI':
                band = self.calc_savi_bands(raster_list)
            self.export_tif(scene_info, band=band, meta=meta)

    def get_rasters(self, scene_info):
        """function for creating and return a list containing all band data"""

        temp_list = []

        for band in scene_info[2]:
            with rasterio.open(self.get_band_filename(band)) as f:
                meta = f.meta
                open_file32 = f.read(1).astype('float32')
                # Set 0's to NaN in the arrays to allow for division
                open_file32[open_file32 == 0] = np.nan
                temp_list.append(open_file32)
        return temp_list, meta

    def stack_tiffs(self, scene_info):
        """stacks the tifs on band list to make a merged tif"""

        output_file = os.path.join(self.output_dir, f'{scene_info[0]}.tif')
        band_list = [self.get_band_filename(band) for band in scene_info[2]]
        # only metadata of first file is read to copy to the merge tiff
        with rasterio.open(band_list[0]) as src:
            meta = src.meta
        meta.update(count=len(band_list))

        with rasterio.open(output_file, 'w', **meta) as dst:
            for i, layer in enumerate(band_list, start=1):
                with rasterio.open(layer) as src1:
                    dst.write_band(i, src1.read(1))
        self.verbose(f'Wrote Out: {output_file}')

    def export_tif(self, scene_info, band, meta):
        """export a band to tif file."""

        out_file = os.path.join(self.output_dir, f'{scene_info[0]}.tif')

        with rasterio.open(out_file, 'w', **meta) as out:
            out.write_band(1, band)
        self.verbose(f'Successfully created: {out_file}')

    @staticmethod
    def calc_ndvi_bands(rasters):
        return np.array((rasters[1] - rasters[0]) / (rasters[1] + rasters[0]))

    @staticmethod
    def calc_savi_bands(rasters):
        return np.array((((rasters[1] - rasters[0]) / (rasters[1] + rasters[0] + 0.5)) * 1.5))

    def get_band_filename(self, band_name):
        return os.path.join(self.output_dir, f'{band_name}-{bands[band_name]}.tif')

    def verbose(self, text, end='\n'):
        if self.verbose_output:
            print(text, end=end)


def main():
    """main interactive interface"""

    # TODO: make this interactive, maybe there are some api to get the url.
    example_url = 'https://landsat-pds.s3.amazonaws.com/c1/L8/046/028/LC08_L1TP_046028_20200908_20200918_01_T1/LC08_L1TP_046028_20200908_20200918_01_T1_B1.TIF'

    parser = argparse.ArgumentParser(
        description='This script downloads Landsat8 imagery from AWS and generates band combinations you designate.',
        usage='\nSelect scene output type(s)\nFor Example: -s 135\n{}\n\n{}'.format(
            '\n'.join([f'{k}: ({v[0]}) - {v[1]}' for k, v in scenes_list.items()]),
            'l8calc.py -s 378 -u https://landsat-pds.s3.amazonaws.com/some/landsat/url.tif -v'),
    )

    parser.add_argument('-s', '--scenes', required=True, help='The scenes you wish to generate. For example: -s 123')
    parser.add_argument('-u', '--url', required=True, default=example_url,
                        help='Copy/paste AWS URL. (Can be found at https://search.remotepixel.ca - Specific band does not matter)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Output progress messages to the console. Default is False.')

    args = parser.parse_args()

    selection = args.scenes

    # some input validation
    try:
        if int(selection.strip()) == 0:
            print('Exiting...')
            return
        else:
            sels = [int(s) for s in sorted(list(set(selection.strip()))) if s not in ['0', '9']]
    except ValueError as e:
        print(f'"{selection}" is invalid scene selection. Try something like "-s 123". Exiting...')
        print(f'Error Text: {e}')
        return

    print(f'Scenes Selected: {[scenes_list[s][0] for s in sels]}')

    L8CALC(url=args.url, output_scenes=sels, verbose=args.verbose)


if __name__ == '__main__':
    main()
