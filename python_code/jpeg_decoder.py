import itertools
import math

import numpy as np
import scipy as scipy
import time
from jpeg_bit_reader import JpegBitReader
from jpeg_common import *
from jpeg_encoder import JpegEncoder

ENCODING_TEST = True


# This is table 5 from https://www.impulseadventure.com/photo/jpeg-huffman-coding.html. It is used for value encoding.
# It is const and does not appear anywhere in the JPG file.
def value_encoding(dc_code: int, additional_bits: int):
    if dc_code == 0:
        return 0
    dc_value_sign = 1 if ((additional_bits & (1 << (dc_code - 1))) > 0) else -1
    if dc_value_sign == 1:
        return additional_bits

    additional_bits_to_add = additional_bits & ((1 << (dc_code - 1)) - 1)

    dc_value_base = 1 - (1 << dc_code)
    ret_val = dc_value_base + additional_bits_to_add
    return ret_val


def put_value_in_matrix_zigzag(matrix, value, index):
    row, col = zig_zag_index(index)
    matrix[row, col] = value


class McuParsedDctComponents:
    def __init__(self, component_ids):
        self.raw_mcus = {i: [] for i in component_ids}
        self.dequantized_mcus = {i: [] for i in component_ids}
        self.mcus_after_idct = {i: [] for i in component_ids}

    def add_mcu(self, comp_id, mcu):
        self.raw_mcus[comp_id].append(mcu)


class JpegDecoder:
    def __init__(self, raw_data, jpeg_decode_metadata):
        self.raw_data = raw_data
        self.jpeg_decode_metadata = jpeg_decode_metadata
        self._decoded_mcu_list = []

        self._full_image_ycbcr = np.zeros((self.jpeg_decode_metadata.height, self.jpeg_decode_metadata.width),
                                          dtype=(float, 3))
        self._full_image_rgb = np.zeros((self.jpeg_decode_metadata.height, self.jpeg_decode_metadata.width),
                                        dtype=(int, 3))

    @staticmethod
    def handle_restart_interval(bit_reader, rst_idx):
        # We expect RSTm
        bit_reader.align()
        marker_mark = bit_reader.read_bits_as_int(JpegBitReader.BYTE_SIZE)
        if marker_mark != 0xFF:
            raise Exception("Expected RST marker during data scan, no marker appears")
        marker_type = bit_reader.read_bits_as_int(JpegBitReader.BYTE_SIZE)
        if marker_type != 0xd0 + rst_idx:
            if 0xd0 <= marker_type <= 0xd7:
                raise Exception(f"Expected RST marker is wrong. Expected {rst_idx} and got {marker_type & 0x0F}")
            else:
                raise Exception(f"Expected RST marker and got different marker of type {marker_type}")
        rst_idx = (rst_idx + 1) % 8
        return rst_idx

    # DROR: mcu == minimal cyber unit
    def huffman_decode_mcus(self, bit_reader, components, n_mcu_horiz, n_mcu_vert, restart_interval):
        rst_idx = 0
        prev_dc_value = {k: 0 for k in components.keys()}
        for mcu_idx in range(n_mcu_horiz * n_mcu_vert):
            if restart_interval is not None and mcu_idx > 0 and (mcu_idx % restart_interval == 0):
                prev_dc_value = {k: 0 for k in components.keys()}
                rst_idx = self.handle_restart_interval(bit_reader, rst_idx)

            if mcu_idx % 1000 == 0:
                debug_print(f"Decoding MCU #{mcu_idx}")
            parsed_mcu = McuParsedDctComponents(components.keys())

            for (comp_id, comp) in components.items():
                for _ in range(comp.number_of_instances_in_mcu):
                    decoded_mcu = self.decode_component_in_mcu(bit_reader, comp.ac_huffman_table,
                                                               comp.dc_huffman_table, prev_dc_value, comp_id)
                    parsed_mcu.add_mcu(comp_id, decoded_mcu)
            self._decoded_mcu_list.append(parsed_mcu)
        bit_reader.align()

    def de_quantize(self, components):
        info_print("Beginning De-quantization")
        for decoded_mcu in self._decoded_mcu_list:
            for (comp_id, comp) in components.items():
                quantization_table = comp.quantization_table
                for comp_mcu in decoded_mcu.raw_mcus[comp_id]:
                    de_quantized_mcu = np.multiply(quantization_table, comp_mcu)
                    decoded_mcu.dequantized_mcus[comp_id].append(de_quantized_mcu)
        info_print("Finish De-quantization")

    def inverse_dct(self, component_keys):
        info_print("Beginning IDCT")
        for decoded_mcu in self._decoded_mcu_list:
            for comp_id in component_keys:
                for comp_mcu in decoded_mcu.dequantized_mcus[comp_id]:
                    after_idct = scipy.fft.idct(scipy.fft.idct(comp_mcu.T, norm='ortho').T, norm='ortho')
                    decoded_mcu.mcus_after_idct[comp_id].append(after_idct)
        info_print("Finished IDCT")

    # GAL
    # Understand 2D-DCT :https://stackoverflow.com/questions/15978468/using-the-scipy-dct-function-to-create-a-2d-dct-ii

    # The jpeg MCUs are simply placed one after the other, therefore decoding them must be in order.
    # Here, each decoding step is done for every MCU, one by one.
    # To decode an MCU one must do the following:
    #   1. Decode the huffman.
    #   2. Convert the bits to dc and ac values (will be further explained by Gal later)
    #   3. Un quantize
    #   4. inverse dct
    #   5. Convert to rgb
    def decode(self):

        bit_reader = JpegBitReader(self.raw_data)
        pixels_mcu_horiz = self.jpeg_decode_metadata.horiz_pixels_in_mcu
        pixels_mcu_vert = self.jpeg_decode_metadata.vert_pixels_in_mcu

        n_mcu_horiz = math.ceil(self.jpeg_decode_metadata.width / pixels_mcu_horiz)
        n_mcu_vert = math.ceil(self.jpeg_decode_metadata.height / pixels_mcu_vert)

        self.huffman_decode_mcus(bit_reader, self.jpeg_decode_metadata.components_to_metadata, n_mcu_horiz, n_mcu_vert,
                                 self.jpeg_decode_metadata.restart_interval)
        info_print("time:", time.time())
        if ENCODING_TEST:
            encoder = JpegEncoder(self.jpeg_decode_metadata)
            res = encoder.encode(self._decoded_mcu_list)

            min_len = min(len(res), len(bit_reader._bytes))
            is_eq = res[:min_len] == bit_reader._bytes[:min_len]
            info_print(f"Equal? {'Yes ☺' if is_eq else 'No!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'}")
        self.de_quantize(self.jpeg_decode_metadata.components_to_metadata)
        info_print("time:", time.time())

        self.inverse_dct(self.jpeg_decode_metadata.components_to_metadata.keys())
        # TODO: The code up until now is true regardless of the number of components,
        #  from here and on it is color space dependent and needs to be fixed because the next function shouldn't be
        self.construct_pixel_map(n_mcu_horiz, pixels_mcu_horiz, pixels_mcu_vert)
        # DROR From here it should be color space dependent
        self._to_rgb()

        return bit_reader.get_byte_location(), self._full_image_rgb, n_mcu_horiz * pixels_mcu_horiz, n_mcu_vert * pixels_mcu_vert

    @staticmethod
    def decode_with_huffman(bit_reader, huff_tree):
        while not huff_tree.is_leaf():
            next_bit = bit_reader.get_bits_as_bool_list(1)[0]
            huff_tree = huff_tree.get_kid(1 if next_bit else 0)
        code = huff_tree.get_value()
        return code

    # How is the DC value encoded: You first use the huffman tree and get a value. We call it DC code. funny name
    # right? Then, you read DC code bits! Like if DC code is 5 you read 5 bits!!! This guy is called
    # additional_bits. You then go to table 5 and look hard hard at the row with DC code. You calculate the
    # offset (good luck with that..) and get DC value. If you want the full details go to this website:
    # https://www.impulseadventure.com/photo/jpeg-huffman-coding.html, Table 5 - Huffman DC Value Encoding
    # Then you remember the DC value is relative to the previous one in the same component so you do the funny
    # offset calculation and Voilà! Your DC value is ready :)
    def decode_dc_for_component_in_mcu(self, dc_tree, bit_reader, prev_dc_value, comp_id):
        #   debug_print('Decoding DC')
        dc_code = self.decode_with_huffman(bit_reader, dc_tree)
        #   debug_print('DC code is ', hex(dc_code))
        assert 0 <= dc_code <= 0x0F, "dc_code must be 0 to 16"
        additional_bits = bit_reader.read_bits_as_int(dc_code)
        dc_value = value_encoding(dc_code, additional_bits)
        dc_value += prev_dc_value[comp_id]
        prev_dc_value[comp_id] = dc_value
        return dc_value

    # First you get a value from the tree like in the DC.
    # Now you got a byte (8 bits). You take the first 4 and call them run_length and the other 4 is name size.
    # Run length is the number of zeros until the next non-zero value, and size we will see.
    # BUT if run_length == size == 0 is called EOB then it says OK no more non-zero values from now on all is zero
    # that's it so we stop (we inited the array to zeros).
    # Another but -- if run_length == 15 and size == 0 is called ZRL means that now come 16 zeros and then continue
    # like business as usual everything good.
    # Otherwise you put run_length zeros zigzagly and then you do again the table 5 SHTIK with size bits you read,
    # which are like additional_bits in the DC explanation. Thus fiasco gives you an AC value which is != 0.
    def decode_ac_for_component_in_mcu(self, ac_tree, bit_reader, decoded_component_data):
        #  debug_print('Decoding AC')
        decoded_idx = 1
        while decoded_idx < 64:
            ac_code = self.decode_with_huffman(bit_reader, ac_tree)
            run_length = (ac_code & 0xf0) >> 4
            size = ac_code & 0x0f
            #  debug_print(f"AC code = {ac_code}, which is ({run_length}, {size})")
            if run_length == 0 and size == 0:
                # This is EOB. No more (we start with a zero matrix)
                debug_print("EOB")
                break
            elif run_length == 15 and size == 0:
                # This is ZRL
                debug_print("ZRL")
                decoded_idx += 16
                continue
            else:
                debug_print(f"Putting {run_length} zero AC values")
                decoded_idx += run_length
                value_aux = bit_reader.read_bits_as_int(size)

                ac_value = value_encoding(size, value_aux)  # This is again table 5!!
                # debug_print(f"AC value = {ac_value}")
                put_value_in_matrix_zigzag(decoded_component_data, ac_value, decoded_idx)
                decoded_idx += 1

    # In the real code make sure that we do not get out of the input range in the place where we huffman-decode
    def decode_component_in_mcu(self, bit_reader, ac_huffman, dc_huffman, prev_dc_value, comp_id):
        decoded_component_data = np.zeros((8, 8))

        dc_value = self.decode_dc_for_component_in_mcu(dc_huffman.get_tree(), bit_reader, prev_dc_value, comp_id)
        put_value_in_matrix_zigzag(decoded_component_data, dc_value, 0)

        self.decode_ac_for_component_in_mcu(ac_huffman.get_tree(), bit_reader, decoded_component_data)

        return decoded_component_data

    def _to_rgb(self):
        info_print("Beginning YCbCr -> RGB transformation")

        def inner_ycbcr_to_rgb(x):
            y = x + 128

            r = math.floor(y[0] + 1.402 * (1.0 * y[2] - 128.0))
            g = math.floor(y[0] - 0.344136 * (1.0 * y[1] - 128.0) - 0.714136 * (1.0 * y[2] - 128.0))
            b = math.floor(y[0] + 1.772 * (1.0 * y[1] - 128.0))
            return r, g, b

        self._full_image_rgb = np.apply_along_axis(inner_ycbcr_to_rgb, 2, self._full_image_ycbcr)
        info_print("Finished YCbCr -> RGB transformation")

    def copy_to_full_image(self, start_row_idx_dst, start_col_idx_dst, dst, comp):
        assert dst.shape[0] + start_row_idx_dst <= self._full_image_ycbcr.shape[0] and \
               dst.shape[1] + start_col_idx_dst <= self._full_image_ycbcr.shape[1] and 0 <= comp <= 2
        self._full_image_ycbcr[start_row_idx_dst: start_row_idx_dst + dst.shape[0],
        start_col_idx_dst:start_col_idx_dst + dst.shape[1], comp] = dst

    def construct_pixel_map(self, n_mcu_horiz, pixels_mcu_horiz, pixels_mcu_vert):
        info_print("constructing pixel map")
        num_sub_mcus_in_row = pixels_mcu_horiz // 8
        num_sub_mcus_in_col = pixels_mcu_vert // 8

        assert (1 <= num_sub_mcus_in_row <= 2 and 1 <= num_sub_mcus_in_col <= 2)

        for decoded_mcu_idx in range(len(self._decoded_mcu_list)):
            decoded_mcu = self._decoded_mcu_list[decoded_mcu_idx]
            # TODO the next is true only for YCbCr, this function should be called construct pixel map from YCbCr
            assert all(len(decoded_mcu.mcus_after_idct[i]) == 1 for i in range(2, 4))

            mcu_row_idx = (decoded_mcu_idx // n_mcu_horiz)
            mcu_col_idx = (decoded_mcu_idx % n_mcu_horiz)

            def smear(orig):
                mat = np.zeros((8 * num_sub_mcus_in_col, 8 * num_sub_mcus_in_row))
                for r, c in itertools.product(range(8 * num_sub_mcus_in_col), range(8 * num_sub_mcus_in_row)):
                    orig_r_idx = r // num_sub_mcus_in_col
                    orig_c_idx = c // num_sub_mcus_in_row
                    mat[r, c] = orig[orig_r_idx, orig_c_idx]
                return mat

            cb_smeared = smear(decoded_mcu.mcus_after_idct[CB_COMP_ID][0])
            cr_smeared = smear(decoded_mcu.mcus_after_idct[CR_COMP_ID][0])
            self.copy_to_full_image((mcu_row_idx * num_sub_mcus_in_col) * 8, (mcu_col_idx * num_sub_mcus_in_row) * 8,
                                    cb_smeared, CB_INDEX_IN_YCBCR)
            self.copy_to_full_image((mcu_row_idx * num_sub_mcus_in_col) * 8, (mcu_col_idx * num_sub_mcus_in_row) * 8,
                                    cr_smeared, CR_INDEX_IN_YCBCR)
            # A sub_mcu is a 8X8 pixel matrix
            for sub_mcu_col_idx, sub_mcu_row_idx in \
                    itertools.product(range(num_sub_mcus_in_row), range(num_sub_mcus_in_col)):
                y_mcu_idx = sub_mcu_row_idx * num_sub_mcus_in_row + sub_mcu_col_idx
                y_mcu = decoded_mcu.mcus_after_idct[Y_COMP_ID][y_mcu_idx]
                self.copy_to_full_image((mcu_row_idx * num_sub_mcus_in_col + sub_mcu_row_idx) * 8,
                                        (mcu_col_idx * num_sub_mcus_in_row + sub_mcu_col_idx) * 8, y_mcu,
                                        Y_INDEX_IN_YCBCR)

        info_print("Done constructing pixel map")
