#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
https://en.wikipedia.org/wiki/Discrete_cosine_transform
"""

import math

import unittest
import random

def get_dct(input_values):
    """
    Apply DCT on list of numbers input_values,
    return list with same number of elements
    """
    matrix_size = len(input_values)
    result = [0.0] * matrix_size
    if matrix_size > 0:
        for outer_index in range(matrix_size):
            for index in range(matrix_size):
                result[outer_index] += (input_values[index]
                                        * math.cos(math.pi / matrix_size
                                                   * outer_index * (index + 0.5)))
        result[0] *= 1.0 / math.sqrt(2.0)
        for index in range(matrix_size):
            result[index] *= math.sqrt(2.0 / matrix_size)
    return result

def get_idct(input_values):
    """Inverse DCT on list of numbers input_values"""
    matrix_size = len(input_values)
    result = [0.0] * matrix_size
    for outer_index in range(matrix_size):
        result[outer_index] = input_values[0] / math.sqrt(2.0)
        for index in range(1, matrix_size):
            result[outer_index] += (input_values[index]
                                    * math.cos(math.pi / matrix_size
                                               * index * (outer_index + 0.5)))
    for index in range(matrix_size):
        result[index] *= math.sqrt(2.0 / matrix_size)
    return result

def get_2d_dct(input_matrix):
    """Apply DCT on 2D matrix (nested list) of numbers input_matrix, return same size matrix"""

    matrix_size = len(input_matrix)

    def c_factor(i):
        if i == 0:
            return 1.0 / math.sqrt(2.0)
        return 1.0

    def cos_term(inner, outer):
        return math.cos(math.pi * outer * (2.0 * inner + 1.0) / (2.0 * matrix_size))

    if matrix_size > 0:
        result = []
        for i in range(matrix_size):
            result.append([0.0] * matrix_size)

        for i in range(matrix_size):
            for j in range(matrix_size):
                for x in range(matrix_size):
                    for y in range(matrix_size):
                        result[i][j] += input_matrix[x][y] * cos_term(x, i) * cos_term(y, j)
                result[i][j] *= c_factor(i) * c_factor(j) * 2.0 / matrix_size

    return result

def get_2d_idct(input_matrix):
    """
    Apply Inverse DCT on 2D matrix (nested list) of
    numbers input_matrix, return same size matrix
    """

    matrix_size = len(input_matrix)

    def c_factor(i):
        if i == 0:
            return 1.0 / math.sqrt(2.0)
        return 1.0

    def cos_term(inner, outer):
        return math.cos(math.pi * inner * (2.0 * outer + 1.0) / (2.0 * matrix_size))

    if matrix_size > 0:
        result = []
        for i in range(matrix_size):
            result.append([0.0] * matrix_size)

        for i in range(matrix_size):
            for j in range(matrix_size):
                for x in range(matrix_size):
                    for y in range(matrix_size):
                        result[i][j] += (c_factor(x) * c_factor(y) * input_matrix[x][y]
                                         * cos_term(x, i) * cos_term(y, j))
                result[i][j] *= 2.0 / matrix_size

    return result

class TestDCT(unittest.TestCase):
    def test_1d(self):
        random.seed()
        for iteration in range(10):
            for list_len in range(100):
                x = list(map(lambda x: random.uniform(-10000, 10000), [0.0] * list_len))
                dct_x = get_dct(x)
                idct_x = get_idct(dct_x)
                for i in range(list_len):
                    self.assertAlmostEqual(x[i], idct_x[i])

    def test_2d(self):
        random.seed()
        for iteration in range(10):
            for list_len in range(2, 16):
                x = []
                for i in range(list_len):
                    x.append(list(map(lambda x: random.uniform(-10000, 10000), [0.0] * list_len)))
                dct_x = get_2d_dct(x)
                idct_x = get_2d_idct(dct_x)
                for i in range(list_len):
                    for j in range(list_len):
                        self.assertAlmostEqual(x[i][j], idct_x[i][j])

if __name__ == '__main__':
    unittest.main()
