#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
https://en.wikipedia.org/wiki/Discrete_cosine_transform
"""

import math

def get_dct( x ):
	"""DCT, return same number of elements"""
	NN = len( x )
	r = [ 0 ] * NN
	for k in range( NN ):
		for n in range( NN ):
			r[ k ] += x[ n ] * math.cos( math.pi / NN * k * ( n + 0.5 ) )
	r[ 0 ] *= 1.0 / math.sqrt( 2.0 )
	for n in range( NN ):
		r[ n ] *= math.sqrt( 2.0 / NN )
	return r

def get_idct( x ):
	"""Inverse DCT"""
	NN = len( x )
	r = [ 0 ] * NN
	for k in range( NN ):
		r[ k ] = x[ 0 ] / math.sqrt( 2.0 )
		for n in range( 1, NN ):
			r[ k ] += x[ n ] * math.cos( math.pi / NN * n * ( k + 0.5 ) )
	for n in range( NN ):
		r[ n ] *= math.sqrt( 2.0 / NN )
	return r
