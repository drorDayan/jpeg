import itertools

import numpy as np
import scipy as scipy

from bmp_writer import BmpWriter
from jpeg_bit_reader import JpegBitReader
from jpeg_common import debug_print


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
    def __init__(self, color_components):
        self.color_components = color_components


class RawDataDecoder:
    def __init__(self):
        self._decoded_mcu_list = []
        self._unsmeared_mcu_matrix = {}  # will be (i,j) -> triplet of 8*8 numpy matrix of ycbcr
        self._rgb_matrix = {}  # will be (i,j) ->triplet 8*8 numpy matrix of rgbs

        self.Cred = 0.299
        self.Cgreen = 0.587
        self.Cblue = 0.114

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
                    debug_print("After IDCT:")
                    debug_print(after_idct)
                    decoded_mcu.mcus_after_idct[comp_id].append(after_idct)

    def decode(self, raw_data, components, n_mcu_horiz, n_mcu_vert, pixels_mcu_horiz, pixels_mcu_verti):

        bit_reader = JpegBitReader(raw_data)
        self.read_raw_mcus(bit_reader, components, n_mcu_horiz, n_mcu_vert)
        self.absoultify_dc_values()
        self.de_quantize(components)
        self.do_idct(components)
        self.unsmear_mcus(components, n_mcu_horiz, n_mcu_vert, pixels_mcu_horiz, pixels_mcu_verti)
        self._to_rgb()

        bmp_writer = BmpWriter()
        bmp_writer.write_from_rgb(self._rgb_matrix, width=n_mcu_horiz * pixels_mcu_horiz,
                                  height=n_mcu_vert * pixels_mcu_verti)

        '''
        TODO:
        * merge unsmeared mcu to a single matrix per color component
        * finish bmp scanning with bigbig matrix
        
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
            debug_print(f"AC code = {ac_code}, which is ({run_length}, {size})")
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
                debug_print(f"AC value = {ac_value}")
                put_value_in_matrix_zigzag(decoded_mcu, ac_value, decoded_idx)
                decoded_idx += 1

        debug_print('Done decoding MCU')

        print(decoded_mcu)
        return decoded_mcu

    def absoultify_dc_values(self):
        print("Yo what about me?")

    def unsmear_mcus(self, components, n_mcu_horiz, n_mcu_vert, pixels_mcu_horiz, pixels_mcu_verti):
        decoded_mcu_idx = 0
        num_unsmeared_horiz = pixels_mcu_horiz // 8
        num_unsmeared_verti = pixels_mcu_verti // 8
        assert (1 <= num_unsmeared_horiz <= 2 and 1 <= num_unsmeared_verti <= 2)

        while decoded_mcu_idx < len(self._decoded_mcu_list):

            decoded_mcu = self._decoded_mcu_list[decoded_mcu_idx]
            assert all(len(decoded_mcu.mcus_after_idct[i]) == 1 for i in range(2, 4))
            for horiz_idx, vert_idx in itertools.product(range(num_unsmeared_horiz), range(num_unsmeared_verti)):
                y_mcu = decoded_mcu.mcus_after_idct[1][num_unsmeared_horiz * vert_idx + horiz_idx]

                def fill_up_unsmeared(orig, horiz_start_offset, vert_start_offset):
                    mat = np.zeros((8, 8))
                    for h, v in itertools.product(range(8), range(8)):
                        h_idx = horiz_start_offset + h // 2
                        v_idx = vert_start_offset + v // 2
                        mat[h, v] = orig[h_idx, v_idx]
                    return mat

                horiz_start_offset = (8 // num_unsmeared_horiz) * horiz_idx
                vert_start_offset = (8 // num_unsmeared_verti) * vert_idx

                cb_unsmeared = fill_up_unsmeared(decoded_mcu.mcus_after_idct[2][0], horiz_start_offset,
                                                 vert_start_offset)
                cr_unsmeared = fill_up_unsmeared(decoded_mcu.mcus_after_idct[3][0], horiz_start_offset,
                                                 vert_start_offset)

                horiz_unsmeared_idx = (decoded_mcu_idx % num_unsmeared_horiz) * (pixels_mcu_horiz // 8) + horiz_idx
                verti_unsmeared_idx = (decoded_mcu_idx // num_unsmeared_horiz) * (pixels_mcu_verti // 8) + vert_idx
                unsmeared = UnsmearedMcu({0: y_mcu, 1: cb_unsmeared, 2: cr_unsmeared})
                self._unsmeared_mcu_matrix[horiz_unsmeared_idx, verti_unsmeared_idx] = unsmeared

            decoded_mcu_idx += 1

        debug_print("Done unsmearing")

    def _to_rgb(self):
        def get_rgb_from_ycbcr(y, cb, cr):
            r = cr * (2 - 2 * self.Cred) + y
            b = cb * (2 - 2 * self.Cblue) + y
            g = (y - self.Cblue * b - self.Cred * r) / self.Cgreen
            return r, g, b

        for (i, j), y_cb_cr_mat in self._unsmeared_mcu_matrix.items():
            self._rgb_matrix[i, j] = {i: np.zeros((8, 8)) for i in range(3)}
            for row, col in itertools.product(range(8), range(8)):
                new_colors = get_rgb_from_ycbcr(*[y_cb_cr_mat.color_components[i][row, col] for i in range(3)])
                assert(all([0 <= new_colors[color_component] + 128 <= 255 for color_component in range(3)]))

                for color_component in range(3):
                    self._rgb_matrix[i, j][color_component][row, col] = new_colors[color_component] + 128

        debug_print("Done YCbCr -> RGB transformation")
