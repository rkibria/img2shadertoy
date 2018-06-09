#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run-length encoding algorithms
"""

def get_repeat_counts( s ):
	"""
	Find sequences of repeated elements in a generic list-like container.
	Returns list containing tuples of the form (count_of_value, value).
	[1, 1, 1, 2, 3, 3] -> [ (3, 1), (1, 2), (2, 3) ]
	"""
	result = []
	last_val = s[ 0 ]
	count = 1
	for i in range( 1, len( s ) ):
		val = s[ i ]
		if ( last_val != None and val != last_val ):
			result.append( ( count, last_val ) )
			last_val = val
			count = 1
		else:
			count += 1
	result.append( ( count, last_val ) )
	return result

def get_sequences( s, min_seq_len = 1 ):
	"""
	Transforms the output of get_repeat_counts() into distinct
	"sequences" and "repeats". Sequences are runs of data that
	do not contain any repetition inside them.
	! This is adjustable using min_seq_len: repeats in the input
	  that are shorter than this value are folded into the
	  previous sequence.
	[ (3, 1), (1, 2), (2, 3) ] -> [ ( ( 'R', 3, 1 ), ( 'S', [2] ), ( 'R', 2, 3 ) ) ]
	"""
	result = []
	sequence = []

	for i in range( len( s ) ):
		count, val = s[ i ]
		if count > min_seq_len:
			if len( sequence ) > 0:
				result.append( ( "S", sequence ) )
				sequence = []
			result.append( ( "R", count, val ) )
		else:
			sequence.extend( [ val ] * count )
	return result
