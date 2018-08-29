#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
https://en.wikipedia.org/wiki/Discrete_cosine_transform
"""

import math

import unittest
import random

def get_dct( x ):
	"""Apply DCT on list of numbers x, return list with same number of elements"""
	NN = len( x )
	r = [ 0.0 ] * NN
	if NN > 0:
		for k in range( NN ):
			for n in range( NN ):
				r[ k ] += x[ n ] * math.cos( math.pi / NN * k * ( n + 0.5 ) )
		r[ 0 ] *= 1.0 / math.sqrt( 2.0 )
		for n in range( NN ):
			r[ n ] *= math.sqrt( 2.0 / NN )
	return r

def get_idct( x ):
	"""Inverse DCT on list of numbers x"""
	NN = len( x )
	r = [ 0.0 ] * NN
	for k in range( NN ):
		r[ k ] = x[ 0 ] / math.sqrt( 2.0 )
		for n in range( 1, NN ):
			r[ k ] += x[ n ] * math.cos( math.pi / NN * n * ( k + 0.5 ) )
	for n in range( NN ):
		r[ n ] *= math.sqrt( 2.0 / NN )
	return r

def get_2d_dct( m ):
	"""Apply DCT on 2D matrix (nested list) of numbers m, return same size matrix"""

	NN = len( m )

	def c_factor( i ):
		if i == 0:
			return 1.0 / math.sqrt( 2.0 )
		else:
			return 1.0

	def cos_term( inner, outer ):
		return math.cos( math.pi * outer * ( 2.0 * inner + 1.0 ) / ( 2.0 * NN ) )

	if NN > 0:
		r = []
		for i in range( NN ):
			r.append( [ 0.0 ] * NN )

		for i in range( NN ):
			for j in range( NN ):
				for x in range( NN ):
					for y in range( NN ):
						r[ i ][ j ] += m[ x ][ y ] * cos_term( x, i ) * cos_term( y, j )
				r[ i ][ j ] *= c_factor( i ) * c_factor( j ) * 2.0 / NN

	return r

def get_2d_idct( m ):
	"""Apply Inverse DCT on 2D matrix (nested list) of numbers m, return same size matrix"""

	NN = len( m )

	def c_factor( i ):
		if i == 0:
			return 1.0 / math.sqrt( 2.0 )
		else:
			return 1.0

	def cos_term( inner, outer ):
		return math.cos( math.pi * inner * ( 2.0 * outer + 1.0 ) / ( 2.0 * NN ) )

	if NN > 0:
		r = []
		for i in range( NN ):
			r.append( [ 0.0 ] * NN )

		for i in range( NN ):
			for j in range( NN ):
				for x in range( NN ):
					for y in range( NN ):
						r[ i ][ j ] += c_factor( x ) * c_factor( y ) * m[ x ][ y ] * cos_term( x, i ) * cos_term( y, j )
				r[ i ][ j ] *= 2.0 / NN

	return r

class Test_DCT( unittest.TestCase ):
	def test_1d( self ):
		random.seed()
		for iteration in range( 10 ):
			for list_len in range( 100 ):
				x = list( map( lambda x: random.uniform( -10000, 10000 ), [ 0.0 ] * list_len ) )
				dct_x = get_dct( x )
				idct_x = get_idct( dct_x )
				for i in range( list_len ):
					self.assertAlmostEqual( x[ i ], idct_x[ i ] )

	def test_2d( self ):
		random.seed()
		for iteration in range( 10 ):
			for list_len in range( 2, 16 ):
				x = []
				for i in range( list_len ):
					x.append( list( map( lambda x: random.uniform( -10000, 10000 ), [ 0.0 ] * list_len ) ) )
				dct_x = get_2d_dct( x )
				idct_x = get_2d_idct( dct_x )
				for i in range( list_len ):
					for j in range( list_len ):
						self.assertAlmostEqual( x[ i ][ j ], idct_x[ i ][ j ] )

if __name__ == '__main__':
	unittest.main()
