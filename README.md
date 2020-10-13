![NIR](https://github.com/AbnormalDistributions/landsat8_scene_calculator/blob/main/new_orleans.png)

# Landsat8 Scene Calculator

This script creates GeoTIFF files of the following:
- Normalized Difference Vegetation Index
- Soil Adjusted Vegetation Index
- Visible Spectrum
- Near Infrared Composite
- Short Wave Infrared
- Agriculture
- Geology
- Bathymetric

# To Use:
```
git clone https://github.com/AbnormalDistributions/landsat8_scene_calculator.git
cd landsat8_scene_calculator
pip install .
l8calc.py -h

# Example Usage
l8calc.py -s 1237 -u https://landsat-pds.s3.amazonaws.com/c1/L8/046/028/LC08_L1TP_046028_20200908_20200918_01_T1/LC08_L1TP_046028_20200908_20200918_01_T1_B1.TIF -v

```

See Resources for more information on the GeoTIFFs that are created.


# Scene Locator
[RemotePixel.ca](https://search.remotepixel.ca)

# Resources
* [(NDVI) Normalized Difference Vegetation Index ](https://www.usgs.gov/core-science-systems/nli/landsat/landsat-normalized-difference-vegetation-index)
* [(SAVI) Soil Adjusted Vegetation Index](https://www.usgs.gov/core-science-systems/nli/landsat/landsat-soil-adjusted-vegetation-index)
* [(Other Combinations) Landsat 8 Bands and Band Combinations](https://gisgeography.com/landsat-8-bands-combinations/)

# Licensing
Code licensed under [MIT License](http://opensource.org/licenses/mit-license.html)

# Contributors 
* [James Steele Howard](https://github.com/AbnormalDistributions) - Original Author
* [Gaurav Atreya](https://github.com/Atreyagaurav)
* [and_viceversa](https://github.com/and-viceversa)

