# Date: 2020/10/08
# Author: James Steele Howard
# This script creates NDVIs, SAVIs, RBG, and NIR images using Landsat8 imagery.

import os
import requests
import rasterio
import numpy as np

# Set the main directory
main_dir = os.getcwd()
# Set and create data directory if it doesn't exist
data_dir = os.path.join(main_dir, 'data')
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    print('data_dir did not exist. New data directory created.')

# Set the base URL for the scene
url_base = 'https://landsat-pds.s3.amazonaws.com/c1/L8/046/028/LC08_L1TP_046028_20200908_20200918_01_T1/LC08_L1TP_046028_20200908_20200918_01_T1_B'

# Define main function that gets user input
def main():
    while True:
        selection = int(input( '-------------------------------\n'
                               'Select a calculation for the scene:\n'
                              '  1) Normalized Difference Vegetation (NDVI)\n'
                              '  2) Soil Adjusted Vegetation Index (SAVI)\n'
                              '  3) Visible Spectrum (RBG)\n'
                              '  4) False Color Infrared (NIR)\n'
                              '  5) *Exit*\n'
                              '-------------------------------\n'
                              'Input number for selection: '))
        # Process user input
        if selection == 1:
            print('NDVI selected.\n'
                  '-------------------------------')
            make_ndvi()
        elif selection == 2:
            print('SAVI selected.\n'
                  '-------------------------------')
            make_savi()
        elif selection == 3:
            print('RGB Image selected.\n'
                  '-------------------------------')
            make_rgb()
        elif selection == 4:
            print('False Color Infrared (NIR) selected.\n'
                  '-------------------------------')
            make_nir()
        elif selection == 5:
            print('Exiting.')
            break

# Define function for obtaining files from internet resource
# and save them to disk
def get_files(band_list):
    # Request the file and save to disk
    for band in band_list:
        TIF_file_name = band +'.TIF'
        # Set location for file to be saved
        output_file = os.path.join(data_dir, TIF_file_name)
        # Set TIF file URL to be requested
        band_url = url_base + TIF_file_name
        # Request file
        print('Attempting to request band ' + str(band) + '.')
        r = requests.get(band_url, allow_redirects=True)
        # Check the status code
        status = r.status_code
        print('Request Status Code for band', band, 'is', status)
        if status == 200:
            # Save the file
            print('Saving band ' + str(band) + ' TIF to data directory.')
            with open(output_file, 'wb') as data:
                data.write(r.content)
        else:
            print('Connection error.')

# Define function for creating and return a list containing
# all band data
def create_list(band_list):
    # Read in the TIF files from disk.
    ## Initialize temp list
    temp_list = []
    counter = 0
    for band in band_list:
        TIF_file_name = band + '.TIF'
        # Set location for file to be imported
        input_file = os.path.join(data_dir, TIF_file_name)
        # Open the files and append to 'temp' list
        open_file = rasterio.open(input_file)
        # Set values to floats to be able to be used in numpy
        open_file32 = open_file.read(1).astype('float32')
        # Set 0's to NaN in the arrays tro allow for division
        open_file32[open_file32==0] = np.nan
        # Append raw data to temporary list
        temp_list.append(open_file32)
    return temp_list, open_file

# Define function for exporting TIF files
def export_tif(file_name, image_data, open_file, band_count):
    ## Set output file
    output_file = os.path.join(data_dir, file_name)
    ## Write the file to disk
    image = rasterio.open(output_file, 'w', driver='Gtiff',
                               height=open_file.height,
                               width=open_file.height,
                               count=band_count, crs=open_file.crs,
                               transform=open_file.transform,
                               dtype='float32')
    index = 1
    for array in image_data:
        image.write(array, index)
        index += 1
    image.close()
    print('**Successfully created', file_name, 'and saved to data directory.**')

# Define function to make NDVI
def make_ndvi():
    # Set the bands required for analysis
    ## 4 is visible red
    ## 5 is near-infrared
    band_list = ['4', '5']
    # Get the files required to perform calculations
    # and save them to disk
    get_files(band_list)
    print('Calculating scene...')
    # Create list containing all band data
    temp_list, open_file = create_list(band_list)
    # Perform calculation for NDVI
    band4 = temp_list[0] # red
    band5 = temp_list[1] # near infrared
    image_data = np.array([(band5-band4)/(band5+band4)])
    # Write TIF to disk
    band_count = 1
    export_tif('NDVI.TIF', image_data, open_file, band_count)
    open_file.close()

def make_savi():
    # Set the bands required for analysis
    ## 4 is visible red
    ## 5 is near-infrared
    band_list = ['4', '5']
    # Get the files required to perform calculations
    # and save them to disk
    get_files(band_list)
    print('Calculating scene...')
    # Create list containing all band data
    temp_list, open_file = create_list(band_list)
    # Perform calculation for SAVI
    band4 = temp_list[0]  # red
    band5 = temp_list[1]  # near infrared
    image_data = np.array([((band5 - band4) / (band5 + band4 + 0.5)) * 1.5])
    # Write TIF to disk
    band_count = 1
    export_tif('SAVI.TIF', image_data, open_file, band_count)
    open_file.close()

def make_rgb():
    # Set the bands required for analysis
    ## Band 4 is visible red
    ## Band 3 is visible green
    ## Band 2 is visible blue
    band_list = ['4', '3', '2']
    # Get the files required to perform calculations and save them to disk
    get_files(band_list)
    print('Calculating scene...')
    # Create list containing all band data
    temp_list, open_file = create_list(band_list)
    # Create an array which holds the bands
    band2 = temp_list[0]  # visible red
    band3 = temp_list[1]  # visible green
    band4 = temp_list[2]  # visible blue
    image_data = np.array(temp_list)
    # Write TIF to disk
    band_count = 3
    export_tif('RGB.TIF', image_data, open_file, band_count)
    open_file.close()

def make_nir():
    # Set the bands required for analysis
    ## Band 5 is near infrared
    ## Band 4 is visible red
    ## Band 3 is visible green
    band_list = ['5', '4', '3']
    # Get the files required to perform calculations
    # and save them to disk
    get_files(band_list)
    print('Calculating scene...')
    # Create list containing all band data
    temp_list, open_file = create_list(band_list)
    # Create an array which holds the bands
    band2 = temp_list[0]  # near infrared
    band3 = temp_list[1]  # visible red
    band4 = temp_list[2]  # visible green
    image_data = np.array(temp_list)
    # Write TIF to disk
    band_count = 3
    export_tif('NIR.TIF', image_data, open_file, band_count)
    open_file.close()

main()
