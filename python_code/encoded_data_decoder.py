"""
This is table 5
"""

# <dc_code> is decoding result gotten by using the huffman tree. <additional_bits> is the <dc_code> that follow right
# after <dc_code> is 8 bits (0..7), <additional_bit> is at most 16 bits (0..15)
# TODO check if it works :O
import bitstream

# 0 <= n <= 63
import numpy as np

from jpeg_common import debug_print


def zig_zag_value(i, j, n=8):
    # upper side of interval
    if i + j >= n:
        return n * n - 1 - zig_zag_value(n - 1 - i, n - 1 - j, n)
    # lower side of interval
    k = (i + j) * (i + j + 1) // 2
    return k + i if (i + j) & 1 else k + j


def zig_zag_index(k, n=8):
    # upper side of interval
    if k >= n * (n + 1) // 2:
        i, j = zig_zag_index(n * n - 1 - k, n)
        return n - 1 - i, n - 1 - j
    # lower side of interval
    i = int((np.sqrt(1 + 8 * k) - 1) / 2)
    j = k - i * (i + 1) // 2
    return (j, i - j) if i & 1 else (i - j, j)


def dc_value_encoding(dc_code: int, additional_bits: int):
    if dc_code == 0:
        return 0
    dc_value_sign = 1 if ((additional_bits & (1 << (dc_code - 1))) > 0) else -1
    additional_bits_to_add = additional_bits & ((1 << (dc_code - 1)) - 1)

    if dc_value_sign:
        dc_value_base = 2 ** (dc_code - 1)
    else:
        dc_value_base = -1 * (2 ** dc_code - 1)

    return dc_value_sign * (dc_value_base + additional_bits_to_add)


def read_bits(num_bits, bit_reader):
    val = 0
    for i in range(num_bits):
        next_bit = bit_reader.read(bool, 1)
        val = val * 2 + (1 if next_bit else 0)
    return val


def put_value_in_matrix_zigzag(matrix, value, index):
    row, col = zig_zag_index(index)
    matrix[row, col] = value
    debug_print(f"MCU: putting {value} in ({row},{col})")


class RawDataDecoder:
    def __init__(self):
        self._decoded_mcu_list = []

    def decode(self, raw_data, components):
        bit_reader = bitstream.BitStream(raw_data)
        idx = 0
        more_mcus_to_read = True
        while more_mcus_to_read:
            for (comp_id, comp) in components.items():
                for comp_no in range(comp.number_of_instances_in_mcu):
                    decoded_mcu = self.decode_component_mcu(bit_reader, comp.ac_huffman_table, comp.dc_huffman_table)
                    self._decoded_mcu_list.append(decoded_mcu)

        '''
        TODO:
        * Implement byte reader so FF00 -> FF and FFx for x >0 -> exception for Dror to handle upupu
        * impl the rest of decode - group mcus that describe the same place inthe pic (should be groups of sum(comp.num_instance_mcu))
        * when time: unquantize, de-DCT and de-Ycbcr in order to get RGB. THen tell dror to do bmp header because he is so
        * smarty pants and knows about headers of bmp.....
        '''
        # don't forget to absolutify dc values

    @staticmethod
    def decode_with_huffman(bit_reader, huff_tree):
        debug_print("Reading bits: ", newline=False)
        while not huff_tree.is_leaf():
            next_bit = bit_reader.read(bool, 1)[0]
            debug_print('1' if next_bit else '0', newline=False)
            huff_tree = huff_tree.get_kid(1 if next_bit else 0)
        code = huff_tree.get_value()
        debug_print("")
        return code

    def decode_component_mcu(self, bit_reader, ac_huffman, dc_huffman):
        dc_tree = dc_huffman.get_tree()
        debug_print('Decoding DC')
        dc_code = self.decode_with_huffman(bit_reader, dc_tree)
        debug_print('DC code is ', hex(dc_code))
        assert (dc_code <= 0x0F)
        additional_bits = read_bits(dc_code, bit_reader)

        dc_value = dc_value_encoding(dc_code, additional_bits)

        decoded_idx = 0

        decoded_mcu = np.zeros((8, 8))
        put_value_in_matrix_zigzag(decoded_mcu, dc_value, decoded_idx)
        decoded_idx += 1
        debug_print('Decoding AC')

        while decoded_idx < 64:
            ac_tree = ac_huffman.get_tree()

            ac_code = self.decode_with_huffman(bit_reader, ac_tree)
            run_length = (ac_code & 0xF0) >> 4
            size = ac_code & 0x0F
            debug_print(f"ac code = {ac_code}, which is ({run_length}, {size})")
            if run_length == 0 and size == 0:
                # This is EOB. No more (we start with a zero matrix)
                debug_print("EOB")
                break
            elif run_length == 15 and size == 0:
                decoded_idx += 16
                debug_print("ZRL")
                # This is ZRL
                continue
            else:
                if run_length > 0:
                    debug_print(f"Putting {run_length} zero AC values")
                for i in range(run_length):
                    put_value_in_matrix_zigzag(decoded_mcu, 0, decoded_idx)
                    decoded_idx += 1
                value_aux = read_bits(size, bit_reader)
                debug_print(f"additional bits = {value_aux}")

                ac_value = dc_value_encoding(size, value_aux)
                debug_print(f"ac value = {ac_value}")
                put_value_in_matrix_zigzag(decoded_mcu, ac_value, decoded_idx)
                decoded_idx += 1

        debug_print('Done decoding MCU')

        print(decoded_mcu)
        return decoded_mcu
