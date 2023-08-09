#!/usr/bin/env python3

# A very simple script that creates a new AICO sky camera image by
# modifying a few of the original input image's headers, adding a few new 
# headers, and deleting a few.  This is required for the files to pass
# fitsverify and contain enough information for CAOM2 requirements.

import argparse
import logging
import os
import re
import shutil
import sys
from astropy.io import fits
from astropy.wcs import Wcsprm

logger = logging.getLogger('aico_weather')

parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter, 
        description=('Rewrite AICO all sky camera images to conform to CAOM2 '
                     'requirements'), 
        epilog=('Example:  aico_weathercam.py 2023_07_05__04_44_09-raw.fits\n'))

parser.add_argument("-d", "--debug", action="store_true", default=False, 
                    help = 'Print extra output during execution')
parser.add_argument('file', metavar = 'FILE', type = str, 
                    help = ('The all sky camera image to reformat.'))

args = parser.parse_args()

if args.debug:
    logger.setLevel(level=logging.DEBUG)
else:
    logger.setLevel(level=logging.INFO)

ch = logging.StreamHandler()
formatter = logging.Formatter(f"%(asctime)s %(levelname)s - %(message)s", 
                              "%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.propagate = False

original_file = args.file
new_file = re.sub(r'(.*)(\.fits)', r'\1_v\2', original_file)
logger.info(f'New FITS-compliant file: {new_file}')
shutil.copy(original_file, new_file)
data, header = fits.getdata(new_file, header=True)

# Add, modify, or delete a few of the original header values.
header['DETECTOR'] = (header['INSTRUME'], 'The detector name')
header['INSTRUME'] = 'All Sky Camera'
header['TELESCOP'] = 'All Sky Camera'
header['OBSERVAT'] = 'AICO'
header['OBJECT'] = 'weather image'
header['OBSTYPE'] = 'object'
header['RELEASE'] = (header['DATE-OBS'], 
                     'When the dataset becomes public')
del header['CDELT1']
del header['CDELT2']
del header['CDELTM1']
del header['CDELTM2']
del header['XPIXELSZ']
del header['YPIXELSZ']

logger.debug(f'FITS headers')
for h in header:
    logger.debug(f'{h} = {header[h]}')

# Write the new, FITS-compliant image
fits.writeto(new_file, data, header, overwrite=True, output_verify='silentfix')

hdu_list = fits.open(new_file, memmap=True, lazy_load_hdus=True)
hdu_list.verify('fix')
hdu_list.close()
headers = [h.header for h in hdu_list]
for header in headers:
    header_string = header.tostring().rstrip()
    header_string = header_string.replace('END' + ' ' * 77, '')
    wcs = Wcsprm(header_string.encode('ascii'))
    logger.debug(wcs)

