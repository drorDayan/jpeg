"""
This is table 5
"""

# <dc_code> is decoding result gotten by using the huffman tree. <additional_bits> is the <dc_code> that follow right
# after <dc_code> is 8 bits (0..7), <additional_bit> is at most 16 bits (0..15)
# TODO check if it works :O

# 0 <= n <= 63
import numpy as np
import scipy as scipy

from jpeg_bit_reader import JpegBitReader
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
        next_bit = bit_reader.get_bits_as_bool_list(1)[0]
        val = val * 2 + (1 if next_bit else 0)
    return val


def put_value_in_matrix_zigzag(matrix, value, index):
    row, col = zig_zag_index(index)
    matrix[row, col] = value
    debug_print(f"MCU: putting {value} in ({row},{col})")


class McuParsedDctComponents:
    def __init__(self):
        self.raw_mcus = {i: [] for i in range(1, 4)}
        self.dequantized_mcus = {i: [] for i in range(1, 4)}
        self.mcus_after_idct = {i: [] for i in range(1, 4)}

    def add_mcu(self, comp_id, mcu):
        self.raw_mcus[comp_id].append(mcu)

class UnsmearedMcu:
    def __init__(self):
        self.color_components = {i : None for i in range(3)}

class RawDataDecoder:
    def __init__(self):
        self._decoded_mcu_list = []
        self._unsmeared_mcu_matrix = {}  #will be (i,j) -> triplet of 8*8 numpy matrix of ycbcr
        self._rgb_matrix = {} #will be (i,j) ->triplet 8*8 numpy matrix of rgbs
    def read_raw_mcus(self, bit_reader, components, n_mcu_horiz, n_mcu_vert):
        idx = 0
        while idx < n_mcu_horiz * n_mcu_vert:
            if idx > 0:
                break
            debug_print(f"Decoding MCU #{idx}")
            parsed_mcu = McuParsedDctComponents()

            for (comp_id, comp) in components.items():
                for comp_no in range(comp.number_of_instances_in_mcu):
                    decoded_mcu = self.decode_component_mcu(bit_reader, comp.ac_huffman_table, comp.dc_huffman_table)
                    parsed_mcu.add_mcu(comp_id, decoded_mcu)
            self._decoded_mcu_list.append(parsed_mcu)

            idx += 1

    def de_quantize(self, components):
        debug_print("Beginning De-quantization")
        for decoded_mcu in self._decoded_mcu_list:
            for (comp_id, comp) in components.items():
                quantization_table = comp.quantization_table
                debug_print("Quantization table:")
                debug_print(quantization_table)
                for comp_mcu in decoded_mcu.raw_mcus[comp_id]:
                    debug_print("Quantized:")
                    debug_print(comp_mcu)
                    de_quantized_mcu = np.multiply(quantization_table, comp_mcu)
                    debug_print("Dequantized:")
                    debug_print(de_quantized_mcu)
                    decoded_mcu.dequantized_mcus[comp_id].append(de_quantized_mcu)

    def do_idct(self, components):
        for decoded_mcu in self._decoded_mcu_list:
            for (comp_id, comp) in components.items():
                for comp_mcu in decoded_mcu.raw_mcus[comp_id]:
                    after_idct = scipy.fft.idct(comp_mcu)
                    debug_print("AFTER IDCT")
                    debug_print(after_idct)
                    decoded_mcu.mcus_after_idct[comp_id].append(after_idct)

    def decode(self, raw_data, components, n_mcu_horiz, n_mcu_vert, pixels_mcu_horiz, pixels_mcu_verti):

        bit_reader = JpegBitReader(raw_data)
        self.read_raw_mcus(bit_reader, components, n_mcu_horiz, n_mcu_vert)
        self.absoultify_dc_values()
        self.de_quantize(components)
        self.do_idct(components)
        self.unsmear_mcus(components, n_mcu_horiz, n_mcu_vert, pixels_mcu_horiz, pixels_mcu_verti)

        '''
        TODO:
        * impl the rest of decode - group mcus that describe the same place inthe pic (should be groups of sum(comp.num_instance_mcu))
        * when time: de-DCT and de-Ycbcr in order to get RGB. THen tell dror to do bmp header because he is so
        * smarty pants and knows about headers of bmp.....
        '''
        # don't forget to absolutify dc values

    @staticmethod
    def decode_with_huffman(bit_reader, huff_tree):
        debug_print("Reading bits: ", newline=False)
        while not huff_tree.is_leaf():
            next_bit = bit_reader.get_bits_as_bool_list(1)[0]
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

    def absoultify_dc_values(self):
        print("Hey what about me?")

    def unsmear_mcus(self, components, n_mcu_horiz, n_mcu_vert, pixels_mcu_horiz, pixels_mcu_verti):
        decoded_mcu_idx = 0
        while decoded_mcu_idx < len(self._decoded_mcu_list):
            num_unsmeared_horiz = pixels_mcu_horiz // 8
            num_unsmeared_verti = pixels_mcu_verti // 8
            assert(1 <= num_unsmeared_horiz <= 2 and 1 <= num_unsmeared_verti <= 2)
            decoded_mcu = self._decoded_mcu_list[decoded_mcu_idx]
            y_mcus = decoded_mcu.mcus_after_idct[1]
            cb_mcus = decoded_mcu.mcus_after_idct[2]
            cr_mcus = decoded_mcu.mcus_after_idct[3]
            assert len(cb_mcus) == 1 and len(cr_mcus) == 1
            for horiz_idx in range(num_unsmeared_horiz):
                for vert_idx in range(num_unsmeared_verti):
                    unsmeared = UnsmearedMcu()
                    y_mcu = y_mcus[num_unsmeared_horiz * vert_idx + horiz_idx]
                    unsmeared.color_components[0] = y_mcu

                    horiz_start_offset = (8 // num_unsmeared_horiz) * horiz_idx
                    vert_start_offset = (8 // num_unsmeared_verti) * vert_idx


                    def fill_up_unsmeared(orig, horiz_start_offset, vert_start_offset):
                        mat = np.zeros((8,8))
                        for h in range(8):
                            for v in range(8):
                                h_idx = horiz_start_offset + h // 2
                                v_idx = vert_start_offset + v // 2
                                mat[h,v] = orig[h_idx, v_idx]
                        return mat

                    cb_unsmeared = fill_up_unsmeared(cb_mcus[0], horiz_start_offset, vert_start_offset)
                    unsmeared.color_components[1] = cb_unsmeared

                    cr_unsmeared = fill_up_unsmeared(cr_mcus[0], horiz_start_offset, vert_start_offset)
                    unsmeared.color_components[2] = cr_unsmeared


                    horiz_unsmeared_idx = (decoded_mcu_idx % num_unsmeared_horiz) * (pixels_mcu_horiz // 8) + horiz_idx
                    verti_unsmeared_idx = (decoded_mcu_idx // num_unsmeared_horiz) * (pixels_mcu_verti // 8) + vert_idx
                    self._unsmeared_mcu_matrix[horiz_unsmeared_idx,verti_unsmeared_idx] = unsmeared

            decoded_mcu_idx += 1

        debug_print("Done unsmearing")