#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bit and bit array helpers
"""

def get_bit(data, bit_index):
    """
    Get bit as integer at index bit_index from bytes array.
    Order is from left to right, so bit_index=0 is MSB.
    """
    if bit_index < 8 * len(data):
        cur_byte = data[bit_index // 8]
        return (cur_byte >> (7 - bit_index % 8)) & 0x1
    raise RuntimeError("Out of bound index %s" % bit_index)

def get_reverse_bits(bytes_array):
    """
    Reverse all bits in arbitrary-length bytes array
    """
    num_bytes = len(bytes_array)
    formatstring = "{0:0%db}" % (num_bytes * 8)
    bit_str = formatstring.format(int.from_bytes(bytes_array, byteorder='big'))
    return int(bit_str[::-1], 2).to_bytes(num_bytes, byteorder='big')

def get_reverse_endian(bytes_array):
    """
    Reverse endianness in arbitrary-length bytes array
    """
    hex_str = bytes_array.hex()
    hex_list = ["".join(i) for i in zip(hex_str[::2], hex_str[1::2])]
    hex_list.reverse()
    return bytes.fromhex("".join(hex_list))

def get_reverse_nibbles(bytes_array):
    """
    Reverse nibbles in arbitrary-length bytes array
    """
    return bytes.fromhex(bytes_array.hex()[::-1])
