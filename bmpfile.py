#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple BMP file loader
"""

import os, sys, logging

from collections import namedtuple

logging.basicConfig( format='bmpfile -- %(message)s' )
logger = logging.getLogger( 'bmpfile' )
logger.setLevel( logging.DEBUG )


BMPData = namedtuple( "BMPData",
	[
		"image_width",
		"image_height",
		"bits_per_pixel",
		"palette_size",
		"palette",
		"row_size",
		"row_data",
	]
	)

def load_bmp( filepath ):
	"""
	See https://en.wikipedia.org/wiki/BMP_file_format
	"""
	with open(filepath, "rb") as binary_file:
		data = binary_file.read()
		logger.info("Read file {0} into memory".format(filepath))

	header_text = data[0:2].decode('utf-8')
	logger.info("BMP header {0}".format(header_text))
	if header_text != "BM":
		raise RuntimeError("File has incorrect header, expected 'BM'")

	filesize = int.from_bytes(data[2:6], byteorder='little')
	logger.info("File size in header {0}".format(filesize))
	if os.path.getsize(filepath) != filesize:
		raise RuntimeError("Header reports incorrect file size")

	imgdata_offset = int.from_bytes(data[10:14], byteorder='little')
	logger.info("Image data offset {0}".format(imgdata_offset))

	dib_header_size = int.from_bytes(data[14:18], byteorder='little')
	logger.info("DIB header size {0}".format(dib_header_size))
	if dib_header_size != 40:
		raise RuntimeError("DIB header size 40 (BITMAPINFOHEADER) expected")

	image_width = int.from_bytes(data[18:22], byteorder='little')
	logger.info("Image width {0}".format(image_width))

	image_height = int.from_bytes(data[22:26], byteorder='little')
	logger.info("Image height {0}".format(image_height))

	color_planes = int.from_bytes(data[26:28], byteorder='little')
	logger.info("Color planes {0}".format(color_planes))
	if color_planes != 1:
		raise RuntimeError("1 color plane expected")

	bits_per_pixel = int.from_bytes(data[28:30], byteorder='little')
	logger.info("Bits per pixel {0}".format(bits_per_pixel))

	compression_method = int.from_bytes(data[30:34], byteorder='little')
	logger.info("Compression method {0}".format(compression_method))
	if compression_method != 0:
		raise RuntimeError("Only compression method 0 is supported")

	image_size = int.from_bytes(data[34:38], byteorder='little')
	logger.info("Raw image size {0}".format(image_size))

	palette_size = int.from_bytes(data[46:50], byteorder='little')
	logger.info("Palette size {0}".format(palette_size))

	palette = [None] * palette_size
	for i in range(palette_size):
		palette_index = 14 + dib_header_size + i * 4
		blue = data[palette_index]
		green = data[palette_index + 1]
		red = data[palette_index + 2]
		palette[i] = (red, green, blue)

	row_size = int(int((bits_per_pixel * image_width + 31) / 32) * 4)
	logger.info("Row size {0} bytes".format(row_size))

	row_data = [None] * image_height
	for i in range(image_height):
		row_index = imgdata_offset + i * row_size
		row_data[i] = data[row_index : row_index + row_size]

	return BMPData(
		image_width,
		image_height,
		bits_per_pixel,
		palette_size,
		palette,
		row_size,
		row_data,
		)
