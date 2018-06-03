#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Convert image to a Shadertoy script
"""

import os, sys, argparse, logging

from collections import namedtuple

BMPData = namedtuple("BMPData",
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

logging.basicConfig(format='-- %(message)s')
logger = logging.getLogger('img2shadertoy')
logger.setLevel(logging.DEBUG)

def loadBMP( filepath ):
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
	if image_width % 32 != 0:
		raise RuntimeError("Image width multiple of 32 expected")

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
	logger.info("Palette {0}".format(str(palette)))

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

def outputHeader( bmp_data ):
	print("const vec2 bitmap_size = vec2({0}, {1});".format(bmp_data.image_width, bmp_data.image_height))
	print("const int longs_per_line = {0};".format(bmp_data.row_size // 4))

def outputPalette( bmp_data ):
	print("const int[] palette = int[] (")
	for i in range(bmp_data.palette_size):
		color = bmp_data.palette[i]
		print("0x00{0:02x}{1:02x}{2:02x}".format(color[2], color[1], color[0]) + ("," if i != bmp_data.palette_size-1 else ""))
	print(");")

def outputBitmap( bmp_data ):
	print("const int[] bitmap = int[] (")
	for i in range(bmp_data.image_height):
		hexvals = []
		for k in range(bmp_data.row_size // 4):
			hexvals.append("0x" + bmp_data.row_data[i][k * 4 : (k+1) * 4].hex())
		print(", ".join(hexvals) + ("," if i != bmp_data.image_height - 1 else ""))
	print(");")

def outputFooter( bmp_data ):
	print("""
int getPaletteIndex( in vec2 uv )
{
	int palette_index = 0;
	ivec2 fetch_pos = ivec2( uv * bitmap_size );
	palette_index = getPaletteIndexXY( fetch_pos );
	return palette_index;
}

vec4 getColorFromPalette( in int palette_index )
{
	int int_color = palette[ palette_index ];
	return vec4( float( int_color & 0xff ) / 255.0,
				float( ( int_color >> 8 ) & 0xff) / 255.0,
				float( ( int_color >> 16 ) & 0xff) / 255.0,
				0 );
}

vec4 getBitmapColor( in vec2 uv )
{
	return getColorFromPalette( getPaletteIndex( uv ) );
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
	vec2 uv = fragCoord / iResolution.y;
	fragColor = getBitmapColor( uv );
}
""")

def processOneBit( bmp_data ):
	outputHeader( bmp_data )
	outputPalette( bmp_data )
	outputBitmap( bmp_data )

	print("""
int getPaletteIndexXY( in ivec2 fetch_pos )
{
	int palette_index = 0;
	if( fetch_pos.x >= 0 && fetch_pos.y >= 0
		&& fetch_pos.x < int( bitmap_size.x ) && fetch_pos.y < int( bitmap_size.y ) )
	{
		int line_index = fetch_pos.y * longs_per_line;

		int long_index = line_index + fetch_pos.x / 32;
		int bitmap_long = bitmap[ long_index ];

		int bit_index = 31 - fetch_pos.x % 32;
		palette_index = ( bitmap_long >> bit_index ) & 1;
	}
	return palette_index;
}
""")

	outputFooter( bmp_data )

def processFourBit( bmp_data ):
	outputHeader( bmp_data )
	outputPalette( bmp_data )
	outputBitmap( bmp_data )

	print("""
int getPaletteIndexXY( in ivec2 fetch_pos )
{
	int palette_index = 0;
	if( fetch_pos.x >= 0 && fetch_pos.y >= 0
		&& fetch_pos.x < int( bitmap_size.x ) && fetch_pos.y < int( bitmap_size.y ) )
	{
		int line_index = fetch_pos.y * longs_per_line;

		int long_index = line_index + fetch_pos.x / 8;
		int bitmap_long = bitmap[ long_index ];

		int nibble_index = 7 - fetch_pos.x % 8;
		palette_index = ( bitmap_long >> ( nibble_index * 4 ) ) & 0xf;
	}
	return palette_index;
}
""")

	outputFooter( bmp_data )

def processEightBit( bmp_data ):
	outputHeader( bmp_data )
	outputPalette( bmp_data )
	outputBitmap( bmp_data )

	print("""
int getPaletteIndexXY( in ivec2 fetch_pos )
{
	int palette_index = 0;
	if( fetch_pos.x >= 0 && fetch_pos.y >= 0
		&& fetch_pos.x < int( bitmap_size.x ) && fetch_pos.y < int( bitmap_size.y ) )
	{
		int line_index = fetch_pos.y * longs_per_line;

		int long_index = line_index + ( fetch_pos.x >> 2 );
		int bitmap_long = bitmap[ long_index ];

		int byte_index = 3 - ( fetch_pos.x & 0x03 );
		palette_index = ( bitmap_long >> ( byte_index << 3 ) ) & 0xff;
	}
	return palette_index;
}
""")

	outputFooter( bmp_data )

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("filename", help="path to bmp file")
	args = parser.parse_args()

	bmp_data = loadBMP( args.filename )

	if bmp_data.bits_per_pixel == 1:
		processOneBit( bmp_data )
	elif bmp_data.bits_per_pixel == 4:
		processFourBit( bmp_data )
	elif bmp_data.bits_per_pixel == 8:
		processEightBit( bmp_data )
	else:
		raise RuntimeError( "Current bits per pixel not supported" )
