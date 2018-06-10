#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bit and bit array helpers
"""

def get_bit( data, i ):
	"""
	Get bit as integer at index i from bytes array.
	Order is from left to right, so i=0 is MSB.
	"""
	if i < 8 * len( data ):
		cur_byte = data[ i // 8 ]
		return ( cur_byte >> ( 7 - i % 8 ) ) & 0x1
	else:
		raise RuntimeError( "Out of bound index %s" % i )

def get_reverse_bits( b ):
	"""
	Reverse all bits in arbitrary-length bytes array
	"""
	num_bytes = len( b )
	formatstring = "{0:0%db}" % ( num_bytes * 8 )
	bitStr = formatstring.format( int.from_bytes( b, byteorder='big' ) )
	return int( bitStr[::-1], 2 ).to_bytes( num_bytes, byteorder='big' )

def get_reverse_endian( b ):
	"""
	Reverse endianness in arbitrary-length bytes array
	"""
	hex_str = b.hex()
	hex_list = [ "".join( i ) for i in zip( hex_str[ ::2 ], hex_str[ 1::2 ] ) ]
	hex_list.reverse()
	return bytes.fromhex( "".join( hex_list ) )

def get_reverse_nibbles( b ):
	"""
	Reverse nibbles in arbitrary-length bytes array
	"""
	return bytes.fromhex( b.hex()[::-1] )
