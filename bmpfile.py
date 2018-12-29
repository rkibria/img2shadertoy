#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple BMP file loader
"""

import os
import logging

from collections import namedtuple

logging.basicConfig(format='bmpfile -- %(message)s')
LOGGER = logging.getLogger('bmpfile')
LOGGER.setLevel(logging.DEBUG)


BMPData = namedtuple("BMPData",
                     ["image_width",
                      "image_height",
                      "bits_per_pixel",
                      "palette_size",
                      "palette",
                      "row_size",
                      "row_data",])

def load_bmp(filepath):
    """
    See https://en.wikipedia.org/wiki/BMP_file_format
    """
    with open(filepath, "rb") as binary_file:
        data = binary_file.read()
        LOGGER.info("Read file %s", filepath)

    header_text = data[0:2].decode('utf-8')
    LOGGER.info("BMP header %s", header_text)
    if header_text != "BM":
        raise RuntimeError("File has incorrect header, expected 'BM'")

    filesize = int.from_bytes(data[2:6], byteorder='little')
    LOGGER.info("File size in header %s", filesize)
    if os.path.getsize(filepath) != filesize:
        raise RuntimeError("Header reports incorrect file size")

    imgdata_offset = int.from_bytes(data[10:14], byteorder='little')
    LOGGER.info("Image data offset %s", imgdata_offset)

    dib_header_size = int.from_bytes(data[14:18], byteorder='little')
    LOGGER.info("DIB header size %s", dib_header_size)
    if dib_header_size != 40:
        raise RuntimeError("DIB header size 40 (BITMAPINFOHEADER) expected")

    image_width = int.from_bytes(data[18:22], byteorder='little')
    LOGGER.info("Image width %s", image_width)

    image_height = int.from_bytes(data[22:26], byteorder='little')
    LOGGER.info("Image height %s", image_height)

    color_planes = int.from_bytes(data[26:28], byteorder='little')
    LOGGER.info("Color planes %s", color_planes)
    if color_planes != 1:
        raise RuntimeError("1 color plane expected")

    bits_per_pixel = int.from_bytes(data[28:30], byteorder='little')
    LOGGER.info("Bits per pixel %s", bits_per_pixel)

    compression_method = int.from_bytes(data[30:34], byteorder='little')
    LOGGER.info("Compression method %s", compression_method)
    if compression_method != 0:
        raise RuntimeError("Only compression method 0 is supported")

    image_size = int.from_bytes(data[34:38], byteorder='little')
    LOGGER.info("Raw image size %s", image_size)

    palette_size = int.from_bytes(data[46:50], byteorder='little')
    LOGGER.info("Palette size %s", palette_size)
    if palette_size == 0:
        raise RuntimeError("Palette size 0 detected: possibly due to MS Paint saving in "
                           "modified format, please try a different program to generate BMP")

    palette = [None] * palette_size
    for i in range(palette_size):
        palette_index = 14 + dib_header_size + i * 4
        blue = data[palette_index]
        green = data[palette_index + 1]
        red = data[palette_index + 2]
        palette[i] = (red, green, blue)

    row_size = int(int((bits_per_pixel * image_width + 31) / 32) * 4)
    LOGGER.info("Row size %s bytes", row_size)

    row_data = [None] * image_height
    for i in range(image_height):
        row_index = imgdata_offset + i * row_size
        row_data[i] = data[row_index : row_index + row_size]

    return BMPData(image_width,
                   image_height,
                   bits_per_pixel,
                   palette_size,
                   palette,
                   row_size,
                   row_data,)
