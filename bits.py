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
	if i < 8 * len(data):
		cur_byte = data[i // 8]
		return (cur_byte >> (7 - i % 8)) & 0x1
	else:
		raise RuntimeError("Out of bound index %s" % i)

def get_reverse_bits_byte( b ):
	bitStr = "{0:08b}".format(int.from_bytes(b, byteorder='little'))
	return int(bitStr[::-1], 2).to_bytes(1, byteorder='little')
