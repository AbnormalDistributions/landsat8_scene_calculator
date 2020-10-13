from setuptools import setup

setup(
    name='landsat8_scene_calculator',
    version='1.0.1',
    scripts=['l8calc.py'],
    url='https://github.com/AbnormalDistributions/landsat8_scene_calculator',
    license='MIT License',
    author='James Steele Howard',
    author_email='james.steele.howard.md@gmail.com',
    description='Download Landsat8 imagery from AWS and generate band combinations you designate.',
    install_requires=['numpy', 'rasterio', 'requests']
)
