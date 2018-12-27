#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Convert image to a Shadertoy script
"""

import os, sys, argparse, logging

import bmpfile
import rle
import bits
import dct

logging.basicConfig(format='-- %(message)s')
logger = logging.getLogger('img2shadertoy')
logger.setLevel(logging.DEBUG)


def output_header(bmp_data):
    print("// Generated with https://github.com/rkibria/img2shadertoy")
    print("const vec2 bitmap_size = vec2({0}, {1});".format(bmp_data.image_width, bmp_data.image_height))

def output_palette(bmp_data):
    print("const int[] palette = int[] (")
    for i in range(bmp_data.palette_size):
        color = bmp_data.palette[i]
        print("0x00{0:02x}{1:02x}{2:02x}".format(color[2], color[1], color[0])+ ("," if i != bmp_data.palette_size-1 else ""))
    print(");")

def reverse_bitmap_order(bmp_data, reverse_type):
    """
    Reverse reverse_type ("bits"/"nibbles"/"endianness")so we save a subtraction in Shadertoy code to get the right pixel
    """
    for i in range(bmp_data.image_height):
        new_row = []
        for k in range(bmp_data.row_size // 4):
            bitmap_long = bmp_data.row_data[i][k * 4 : (k + 1)* 4]
            if reverse_type == "bits":
                bitmap_long = bits.get_reverse_bits(bitmap_long)
            elif reverse_type == "nibbles":
                bitmap_long = bits.get_reverse_nibbles(bitmap_long)
            elif reverse_type == "endianness":
                bitmap_long = bits.get_reverse_endian(bitmap_long)
            else:
                raise RuntimeError("Unknown reversal type %s" % reverse_type)
            new_row.append(bitmap_long)
        bmp_data.row_data[i] = bytes().join(new_row)

def output_bitmap(bmp_data):
    print("const int longs_per_line = {0};".format(bmp_data.row_size // 4))
    print("const int[] bitmap = int[] (")
    for i in range(bmp_data.image_height):
        hexvals = []
        for k in range(bmp_data.row_size // 4):
            bitmap_long = bmp_data.row_data[i][k * 4 : (k + 1)* 4]
            hexvals.append("0x" + bitmap_long.hex())
        print(", ".join(hexvals)+ ("," if i != bmp_data.image_height - 1 else ""))
    print(");")

def output_footer():
    print("""
int getPaletteIndex(in vec2 uv)
{
    int palette_index = 0;
    ivec2 fetch_pos = ivec2(uv * bitmap_size);
    palette_index = getPaletteIndexXY(fetch_pos);
    return palette_index;
}

vec4 getColorFromPalette(in int palette_index)
{
    int int_color = palette[palette_index];
    return vec4(float(int_color & 0xff)/ 255.0,
                float((int_color >> 8)& 0xff)/ 255.0,
                float((int_color >> 16)& 0xff)/ 255.0,
                0);
}

vec4 getBitmapColor(in vec2 uv)
{
    return getColorFromPalette(getPaletteIndex(uv));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = fragCoord / bitmap_size;
    fragColor = getBitmapColor(uv);
}
""")

def output_rle(encoded):
    print("const int[] rle = int[] (")
    hexvals = []
    for k in range(len(encoded)// 4):
        long_val = encoded[k * 4 : (k + 1)* 4]
        long_val = bits.get_reverse_endian(long_val)
        hexvals.append("0x" + long_val.hex())
    print(",\n".join(hexvals))
    print(");")

    print("""
const int rle_len_bytes = rle.length()<< 2;

int get_rle_byte(in int byte_index)
{
    int long_val = rle[byte_index >> 2];
    return (long_val >> ((byte_index & 0x03)<< 3))& 0xff;
}

int get_uncompr_byte(in int byte_index)
{
    int rle_index = 0;
    int cur_byte_index = 0;
    while(rle_index < rle_len_bytes)
    {
        int cur_rle_byte = get_rle_byte(rle_index);
        bool is_sequence = int(cur_rle_byte & 0x80)== 0;
        int count = (cur_rle_byte & 0x7f)+ 1;

        if(byte_index >= cur_byte_index && byte_index < cur_byte_index + count)
        {
            if(is_sequence)
            {
                return get_rle_byte(rle_index + 1 + (byte_index - cur_byte_index));
            }
            else
            {
                return get_rle_byte(rle_index + 1);
            }
        }
        else
        {
            if(is_sequence)
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
""")

def sequences_to_bytes(seq, value_op = None):
    """
    Transforms result of rle.get_sequences()into a byte array.
    Encoding:
    - repeats start with a byte whose MSB is 1 and the lower bits are the count,
      followed by the value to repeat.
    - sequences start with a byte whose MSB is 0 and the lower bits are the sequence length,
      followed by that number of bytes of the sequence.
    """
    result = []
    for s in seq:
        if s[0] == "R":
            count = s[1]
            val = s[2]
            while count != 0:
                cur_reps = min(128, count)
                result.append((0x80 | (cur_reps - 1)).to_bytes(1, "little"))
                store_val = val.to_bytes(1, "little")
                if value_op:
                    store_val = value_op(store_val)
                result.append(store_val)
                count -= cur_reps
        else:
            sequence = s[1]
            seq_len = len(sequence)
            seq_i = 0
            while seq_len != 0:
                cur_len = min(128, seq_len)
                result.append((cur_len - 1).to_bytes(1, "little"))
                for v in sequence[seq_i : seq_i + cur_len]:
                    store_val = v.to_bytes(1, "little")
                    if value_op:
                        store_val = value_op(store_val)
                    result.append(store_val)
                seq_i += cur_len
                seq_len -= cur_len
    return b''.join(result)

def process_one_bit(bmp_data, rle_enabled):
    output_header(bmp_data)
    output_palette(bmp_data)

    if rle_enabled:
        bitmap = bytes().join(bmp_data.row_data)
        seq = rle.get_sequences(rle.get_repeat_counts(bitmap), 3)
        encoded = sequences_to_bytes(seq, bits.get_reverse_bits)

        output_rle(encoded)

        print("""
int getPaletteIndexXY(in ivec2 fetch_pos)
{
    int palette_index = 0;
    if(fetch_pos.x >= 0 && fetch_pos.y >= 0
        && fetch_pos.x < int(bitmap_size.x)&& fetch_pos.y < int(bitmap_size.y))
    {
        int uncompr_byte_index = fetch_pos.y * (int(bitmap_size.x)>> 3)
            + (fetch_pos.x >> 3);
        int uncompr_byte = get_uncompr_byte(uncompr_byte_index);

        int bit_index = fetch_pos.x & 0x07;
        palette_index = (uncompr_byte >> bit_index)& 1;
    }
    return palette_index;
}
""")
    else:
        reverse_bitmap_order(bmp_data, "bits")
        output_bitmap(bmp_data)
        print("""
int getPaletteIndexXY(in ivec2 fetch_pos)
{
    int palette_index = 0;
    if(fetch_pos.x >= 0 && fetch_pos.y >= 0
        && fetch_pos.x < int(bitmap_size.x)&& fetch_pos.y < int(bitmap_size.y))
    {
        int line_index = fetch_pos.y * longs_per_line;

        int long_index = line_index + (fetch_pos.x >> 5);
        int bitmap_long = bitmap[long_index];

        int bit_index = fetch_pos.x & 0x1f;
        palette_index = (bitmap_long >> bit_index)& 1;
    }
    return palette_index;
}
""")

    output_footer()

def process_four_bit(bmp_data, rle_enabled):
    output_header(bmp_data)
    output_palette(bmp_data)

    if rle_enabled:
        bitmap = bytes().join(bmp_data.row_data)
        seq = rle.get_sequences(rle.get_repeat_counts(bitmap), 3)
        encoded = sequences_to_bytes(seq, bits.get_reverse_nibbles)

        output_rle(encoded)

        print("""
int getPaletteIndexXY(in ivec2 fetch_pos)
{
    int palette_index = 0;
    if(fetch_pos.x >= 0 && fetch_pos.y >= 0
        && fetch_pos.x < int(bitmap_size.x)&& fetch_pos.y < int(bitmap_size.y))
    {
        int uncompr_byte_index = fetch_pos.y * (int(bitmap_size.x)>> 1)
            + (fetch_pos.x >> 1);

        int uncompr_byte = get_uncompr_byte(uncompr_byte_index);

        int nibble_index = fetch_pos.x & 0x01;
        palette_index = (uncompr_byte >> (nibble_index << 2))& 0xf;
    }
    return palette_index;
}
""")
    else:
        reverse_bitmap_order(bmp_data, "nibbles")
        output_bitmap(bmp_data)

        print("""
int getPaletteIndexXY(in ivec2 fetch_pos)
{
    int palette_index = 0;
    if(fetch_pos.x >= 0 && fetch_pos.y >= 0
        && fetch_pos.x < int(bitmap_size.x)&& fetch_pos.y < int(bitmap_size.y))
    {
        int line_index = fetch_pos.y * longs_per_line;

        int long_index = line_index + (fetch_pos.x >> 3);
        int bitmap_long = bitmap[long_index];

        int nibble_index = fetch_pos.x & 0x07;
        palette_index = (bitmap_long >> (nibble_index << 2))& 0xf;
    }
    return palette_index;
}
""")

    output_footer()

# https://en.wikipedia.org/wiki/JPEG#Quantization
QUANT_MTX = [
    [16, 11, 10, 16,],
    [12, 12, 14, 19,],
    [14, 13, 16, 24,],
    [14, 17, 22, 29,],
    ]

def get_quantized_dct_block(dct_output_block_size, compressed_dct_block):
    quantized_block = []
    for y in range(dct_output_block_size):
        quantized_row = []
        for x in range(dct_output_block_size):
            unquantized = compressed_dct_block[y][x]
            quant_factor = QUANT_MTX[y][x]
            quantized = int(round(unquantized / quant_factor))
            quantized_row.append(quantized)
        quantized_block.append(quantized_row)
    return quantized_block

def get_quantized_ints_block(dct_output_block_size, quantized_block):
    ints_block = []
    for y in range(dct_output_block_size):
        current_int = 0
        for x in range(dct_output_block_size):
            quantized = quantized_block[y][x]
            print(quantized)
            contrib = (quantized << (x * 8))& (0xff << (x * 8))
            print(contrib)
            current_int |= contrib
            print("")
        print("---")
        print(current_int.to_bytes(4, byteorder='big'))
        ints_block.append(current_int)
    return ints_block

def process_eight_bit(bmp_data, use_dct):
    if use_dct:
        dct_input_block_size = 8
        dct_output_block_size = 4

        if bmp_data.image_height % dct_input_block_size != 0:
            raise RuntimeError("Image height multiple of %d expected" % dct_input_block_size)

        output_header(bmp_data)

        dct_columns = bmp_data.image_width // dct_input_block_size
        dct_rows = bmp_data.image_height // dct_input_block_size

        print("#define PI 3.141592653589793")
        print("const int pixels_per_dct_block = {0};".format(dct_input_block_size))
        print("const int dct_block_size = {0};".format(dct_output_block_size))
        print("const int dct_columns = {0};".format(dct_columns))
        print("const int dct_rows = {0};".format(dct_rows))

        dct_compressed_data = []
        for y in range(dct_rows):
            dct_compressed_row = []
            row_bytes = bmp_data.row_data[y * dct_input_block_size : (y + 1)* dct_input_block_size]
            for x in range(dct_columns):
                dct_block_bytes = []
                for i in range(dct_input_block_size):
                    dct_block_bytes.append(row_bytes[i][x * dct_input_block_size : (x + 1)* dct_input_block_size])

                shifted_colors = []
                for block_bytes in dct_block_bytes:
                    color_vals = [(sum(bmp_data.palette[i])/ 3.0)for i in block_bytes]
                    shifted_colors.append([(i - 128)for i in color_vals])

                dct_block = dct.get_2d_dct(shifted_colors)

                compressed_dct_block = []
                for i in range(dct_output_block_size):
                    compressed_dct_block.append(dct_block[i][: dct_output_block_size])

                dct_compressed_row.append(compressed_dct_block)
            dct_compressed_data.append(dct_compressed_row)

        print("const float[] dct = float[] (")
        for y in range(dct_rows):
            for x in range(dct_columns):
                dct_block = dct_compressed_data[y][x]
                print(dct_block)
                quantized_block = get_quantized_dct_block(dct_output_block_size, dct_block)
                print(quantized_block)
                ints_block = get_quantized_ints_block(dct_output_block_size, quantized_block)
                print(ints_block)
                # for row_index in range(dct_output_block_size):
                    # print(", ".join(map(str, dct_block[row_index]))
                            # + ("" if (y == (dct_rows - 1)and (x == dct_columns - 1)and (row_index == dct_output_block_size - 1))else ",")
                            #)
                print()
            print()
        print(");")
        sys.exit(0)

        print("""
float get_dct_val(in int start, in int x, in int y)
{
    return (x < dct_block_size && y < dct_block_size)? dct[start + y * dct_block_size + x] : 0. ;
}

float c_factor(in int i)
{
    return (i == 0)?  (1.0 / sqrt(2.0)): 1.0;
}

float cos_term(in int inner, in int outer)
{
    return cos(PI * float(inner)* (2.0 * float(outer)+ 1.0)/ (2.0 * float(pixels_per_dct_block)));
}

float get_idct(in int start, in int i, in int j)
{
    float NN = float(pixels_per_dct_block);
    float r = 0.;

    for(int x = 0; x < pixels_per_dct_block; ++x)
    {
        for(int y = 0; y < pixels_per_dct_block; ++y)
        {
            r += c_factor(x)* c_factor(y)* get_dct_val(start, x, y)* cos_term(x, i)* cos_term(y, j);
        }
    }

    r *= 2. / NN;
    return r;
}

vec4 getBitmapColor(in vec2 uv)
{
    vec4 col = vec4(0);
    ivec2 fetch_pos = ivec2(uv * bitmap_size);
    if(fetch_pos.x >= 0 && fetch_pos.y >= 0
        && fetch_pos.x < int(bitmap_size.x)&& fetch_pos.y < int(bitmap_size.y))
    {
        int dct_row = fetch_pos.y / pixels_per_dct_block;
        int dct_col = fetch_pos.x / pixels_per_dct_block;
        const int values_per_dct_block = dct_block_size * dct_block_size;
        int dct_values_per_row = values_per_dct_block * dct_columns;
        int dct_block_index = dct_row * dct_values_per_row + dct_col * values_per_dct_block;
        int pixel_x = fetch_pos.x % pixels_per_dct_block;
        int pixel_y = fetch_pos.y % pixels_per_dct_block;
        float idct = get_idct(dct_block_index, pixel_x, pixel_y);
        col = vec4((idct + 128.)/ 255.);
    }
    return col;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = fragCoord / iResolution.y;
    fragColor = getBitmapColor(uv);
}
""")
    else:
        output_header(bmp_data)
        output_palette(bmp_data)

        reverse_bitmap_order(bmp_data, "endianness")
        output_bitmap(bmp_data)

        print("""
int getPaletteIndexXY(in ivec2 fetch_pos)
{
    int palette_index = 0;
    if(fetch_pos.x >= 0 && fetch_pos.y >= 0
        && fetch_pos.x < int(bitmap_size.x)&& fetch_pos.y < int(bitmap_size.y))
    {
        int line_index = fetch_pos.y * longs_per_line;

        int long_index = line_index + (fetch_pos.x >> 2);
        int bitmap_long = bitmap[long_index];

        int byte_index = fetch_pos.x & 0x03;
        palette_index = (bitmap_long >> (byte_index << 3))& 0xff;
    }
    return palette_index;
}
""")

        output_footer()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="path to bmp file")
    parser.add_argument("--rle", help="enable RLE encoding", action="store_true")
    parser.add_argument("--dct", help="enable DCT encoding (8 bit only, converts to grayscale)", action="store_true")
    # parser.add_argument("--bw", help="convert to black & white (avoids storing palette)", action="store_true")
    args = parser.parse_args()

    bmp_data = bmpfile.load_bmp(args.filename)
    if bmp_data.image_width % 32 != 0:
        raise RuntimeError("Image width multiple of 32 expected")

    if bmp_data.bits_per_pixel == 1:
        process_one_bit(bmp_data, args.rle)
    elif bmp_data.bits_per_pixel == 4:
        process_four_bit(bmp_data, args.rle)
    elif bmp_data.bits_per_pixel == 8:
        if args.rle:
            raise RuntimeError("RLE currently not supported for this format")
        process_eight_bit(bmp_data, args.dct)
    else:
        raise RuntimeError("Current bits per pixel not supported")
