![NIR](https://github.com/AbnormalDistributions/landsat8_scene_calculator/blob/main/new_orleans.png)

# Landsat8 Scene Calculator

This script creates GeoTIFF files of the following:

| Calculation                                | Formula / Band Combinations                           |
| ---                                        | ---                                                   |
| Normalized Difference Vegetation Index     | (Band 5 – Band 4) / (Band 5 + Band 4)                 |
| Soil Adjusted Vegetation Index             | ((Band 5 – Band 4) / (Band 5 + Band 4 + 0.5)) * (1.5) |
| Visible Spectrum (Natural Color) Composite | Bands: 4, 3, 2                                        |
| Color / Near Infrared Composite            | Bands: 5, 4, 3                                        |
| Short-Wave Infrared Composite              | Bands: 7, 6, 4                                        |
| Agriculture Composite                      | Bands: 6, 5, 2                                        |
| Geology Composite                          | Bands: 7, 6, 2                                        |
| Bathymetric Composite                      | Bands: 4, 3, 1                                        |

# To Use:
1. Find the aread of interest using [RemotePixel.ca](https://search.remotepixel.ca).
2. Change the url to *url_base* minus the last character of the url and file extension (TODO: make it interactive)
3. Run the script.

See Resources for more information on the GeoTIFFs that are created.


# Area of Interest Locator:
[RemotePixel.ca](https://search.remotepixel.ca)

# Resources:
* [(NDVI) Normalized Difference Vegetation Index ](https://www.usgs.gov/core-science-systems/nli/landsat/landsat-normalized-difference-vegetation-index)
* [(SAVI) Soil Adjusted Vegetation Index](https://www.usgs.gov/core-science-systems/nli/landsat/landsat-soil-adjusted-vegetation-index)
* [(Combinations) Landsat 8 Bands and Band Combinations](https://gisgeography.com/landsat-8-bands-combinations/)

# Licensing:
Code licensed under [MIT License](http://opensource.org/licenses/mit-license.html)

# Contributors: 
* [James Steele Howard](https://github.com/AbnormalDistributions) - Original Author
* [Gaurav Atreya](https://github.com/Atreyagaurav)

