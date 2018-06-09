#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Convert image to a Shadertoy script
"""

import os, sys, argparse, logging

import bmpfile
import rle
import bits

logging.basicConfig( format='-- %(message)s' )
logger = logging.getLogger( 'img2shadertoy' )
logger.setLevel( logging.DEBUG )


def output_header( bmp_data ):
	print("const vec2 bitmap_size = vec2({0}, {1});".format(bmp_data.image_width, bmp_data.image_height))

def output_palette( bmp_data ):
	print("const int[] palette = int[] (")
	for i in range(bmp_data.palette_size):
		color = bmp_data.palette[i]
		print("0x00{0:02x}{1:02x}{2:02x}".format(color[2], color[1], color[0]) + ("," if i != bmp_data.palette_size-1 else ""))
	print(");")

def output_bitmap( bmp_data ):
	print("const int longs_per_line = {0};".format(bmp_data.row_size // 4))
	print("const int[] bitmap = int[] (")
	for i in range(bmp_data.image_height):
		hexvals = []
		for k in range(bmp_data.row_size // 4):
			bitmapLong = bmp_data.row_data[i][k * 4 : (k+1) * 4]
			if bmp_data.bits_per_pixel == 1:
				# Reverse bits
				bitStr = "{0:032b}".format(int.from_bytes(bitmapLong, byteorder='little'))
				bitmapLong = int(bitStr[::-1], 2).to_bytes(4, byteorder='little')
			elif bmp_data.bits_per_pixel == 4:
				# Reverse nibbles
				bitmapLong = int(bitmapLong.hex()[::-1], 16).to_bytes(4, byteorder='big')
			elif bmp_data.bits_per_pixel == 8:
				# Reverse endianness
				bitmapLong = int.from_bytes(bitmapLong, byteorder='little').to_bytes(4, byteorder='big')
			hexvals.append("0x" + bitmapLong.hex())
		print(", ".join(hexvals) + ("," if i != bmp_data.image_height - 1 else ""))
	print(");")

def output_footer( bmp_data ):
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
	vec2 uv = fragCoord / bitmap_size;
	fragColor = getBitmapColor( uv );
}
""")

def sequences_to_bytes( seq ):
	"""
	Transforms result of rle.get_sequences() into a byte array.
	Encoding:
	- repeats start with a byte whose MSB is 1 and the lower bits are the count,
	  followed by the value to repeat.
	- sequences start with a byte whose MSB is 0 and the lower bits are the sequence length,
	  followed by that number of bytes of the sequence.
	"""
	result = []
	for s in seq:
		if s[ 0 ] == "R":
			count = s[ 1 ]
			val = s[ 2 ]
			while count != 0:
				cur_reps = min( 128, count )
				result.append( ( 0x80 | ( cur_reps - 1 ) ).to_bytes( 1, "little" ) )
				result.append( bits.get_reverse_bits_byte( val.to_bytes( 1, "little" ) ) )
				count -= cur_reps
		else:
			sequence = s[ 1 ]
			seq_len = len( sequence )
			seq_i = 0
			while seq_len != 0:
				cur_len = min( 128, seq_len )
				result.append( ( cur_len - 1).to_bytes( 1, "little" ) )
				for v in sequence[ seq_i : seq_i + cur_len ]:
					result.append( bits.get_reverse_bits_byte( v.to_bytes( 1, "little" ) ) )
				seq_i += cur_len
				seq_len -= cur_len
	return b''.join( result )

def process_one_bit( bmp_data, rle_enabled ):
	output_header( bmp_data )
	output_palette( bmp_data )

	if rle_enabled:
		bitmap = bytes().join( bmp_data.row_data )
		seq = rle.get_sequences( rle.get_repeat_counts( bitmap ), 3 )
		encoded = sequences_to_bytes( seq )

		print( "const int[] rle = int[] (" )
		hexvals = []
		for k in range( len( encoded ) // 4 ):
			long_val = encoded[ k * 4 : ( k + 1 ) * 4 ]
			long_val = int.from_bytes( long_val, byteorder='little' ).to_bytes( 4, byteorder='big' )
			hexvals.append( "0x" + long_val.hex() )
		print( ",\n".join( hexvals ) )
		print( ");" )
		print("""
const int rle_len_bytes = rle.length() << 2;

int get_rle_byte( in int byte_index )
{
	int long_val = rle[ byte_index >> 2 ];
	return ( long_val >> ( ( byte_index & 0x03 ) << 3 ) ) & 0xff;
}

int get_uncompr_byte( in int byte_index )
{
	int rle_index = 0;
	int cur_byte_index = 0;
	while( rle_index < rle_len_bytes )
	{
		int cur_rle_byte = get_rle_byte( rle_index );
		bool is_sequence = int( cur_rle_byte & 0x80 ) == 0;
		int count = ( cur_rle_byte & 0x7f ) + 1;

		if( byte_index >= cur_byte_index && byte_index < cur_byte_index + count )
		{
			if( is_sequence )
			{
				return get_rle_byte( rle_index + 1 + ( byte_index - cur_byte_index ) );
			}
			else
			{
				return get_rle_byte( rle_index + 1 );
			}
		}
		else
		{
			if( is_sequence )
			{
				rle_index += count + 1;
				cur_byte_index += count;
			}
			else
			{
				rle_index += 2;
				cur_byte_index += count;
			}
		}
	}

	return 0;
}

int getPaletteIndexXY( in ivec2 fetch_pos )
{
	int palette_index = 0;
	if( fetch_pos.x >= 0 && fetch_pos.y >= 0
		&& fetch_pos.x < int( bitmap_size.x ) && fetch_pos.y < int( bitmap_size.y ) )
	{
		int uncompr_byte_index = fetch_pos.y * ( int( bitmap_size.x ) >> 3 )
			+ ( fetch_pos.x >> 3);
		int uncompr_byte = get_uncompr_byte( uncompr_byte_index );

		int bit_index = fetch_pos.x & 0x07;
		palette_index = ( uncompr_byte >> bit_index ) & 1;
	}
	return palette_index;
}
""")
	else:
		output_bitmap( bmp_data )
		print("""
int getPaletteIndexXY( in ivec2 fetch_pos )
{
	int palette_index = 0;
	if( fetch_pos.x >= 0 && fetch_pos.y >= 0
		&& fetch_pos.x < int( bitmap_size.x ) && fetch_pos.y < int( bitmap_size.y ) )
	{
		int line_index = fetch_pos.y * longs_per_line;

		int long_index = line_index + ( fetch_pos.x >> 5 );
		int bitmap_long = bitmap[ long_index ];

		int bit_index = fetch_pos.x & 0x1f;
		palette_index = ( bitmap_long >> bit_index ) & 1;
	}
	return palette_index;
}
""")

	output_footer( bmp_data )

def process_four_bit( bmp_data ):
	output_header( bmp_data )
	output_palette( bmp_data )
	output_bitmap( bmp_data )

	print("""
int getPaletteIndexXY( in ivec2 fetch_pos )
{
	int palette_index = 0;
	if( fetch_pos.x >= 0 && fetch_pos.y >= 0
		&& fetch_pos.x < int( bitmap_size.x ) && fetch_pos.y < int( bitmap_size.y ) )
	{
		int line_index = fetch_pos.y * longs_per_line;

		int long_index = line_index + ( fetch_pos.x >> 3 );
		int bitmap_long = bitmap[ long_index ];

		int nibble_index = fetch_pos.x & 0x07;
		palette_index = ( bitmap_long >> ( nibble_index << 2 ) ) & 0xf;
	}
	return palette_index;
}
""")

	output_footer( bmp_data )

def process_eight_bit( bmp_data ):
	output_header( bmp_data )
	output_palette( bmp_data )
	output_bitmap( bmp_data )

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

		int byte_index = fetch_pos.x & 0x03;
		palette_index = ( bitmap_long >> ( byte_index << 3 ) ) & 0xff;
	}
	return palette_index;
}
""")

	output_footer( bmp_data )

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("filename", help="path to bmp file")
	parser.add_argument("--rle", help="enable RLE encoding", action="store_true")
	args = parser.parse_args()

	bmp_data = bmpfile.load_bmp( args.filename )
	if bmp_data.image_width % 32 != 0:
		raise RuntimeError("Image width multiple of 32 expected")

	if bmp_data.bits_per_pixel == 1:
		process_one_bit( bmp_data, args.rle )
	elif bmp_data.bits_per_pixel == 4:
		if args.rle:
			raise RuntimeError( "RLE currently not supported for this format" )
		process_four_bit( bmp_data )
	elif bmp_data.bits_per_pixel == 8:
		if args.rle:
			raise RuntimeError( "RLE currently not supported for this format" )
		process_eight_bit( bmp_data )
	else:
		raise RuntimeError( "Current bits per pixel not supported" )
