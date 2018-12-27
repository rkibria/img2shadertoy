#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run-length encoding algorithms
"""

def get_repeat_counts(sequence):
    """
    Find sequences of repeated elements in a generic list-like container.
    Returns list containing tuples of the form (count_of_value, value).
    [1, 1, 1, 2, 3, 3] -> [(3, 1), (1, 2), (2, 3)]
    """
    result = []
    last_val = sequence[0]
    count = 1
    for i in range(1, len(sequence)):
        val = sequence[i]
        if last_val not in (None, val):
            result.append((count, last_val))
            last_val = val
            count = 1
        else:
            count += 1
    result.append((count, last_val))
    return result

def get_sequences(sequence, min_seq_len=1):
    """
    Transforms the output of get_repeat_counts() into distinct
    "sequences" and "repeats". Sequences are runs of data that
    do not contain any repetition inside them.
    ! This is adjustable using min_seq_len: repeats in the input
      that are shorter than this value are folded into the
      previous sequence.
    [(3, 1), (1, 2), (2, 3)] -> [(('R', 3, 1), ('S', [2]), ('R', 2, 3))]
    """
    result = []
    build_seq = []

    for count, val in sequence:
        if count > min_seq_len:
            if build_seq:
                result.append(("S", build_seq))
                build_seq = []
            result.append(("R", count, val))
        else:
            build_seq.extend([val] * count)
    return result
