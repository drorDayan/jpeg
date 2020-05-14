import math

from jpeg_bit_writer import JpegBitWriter
from jpeg_common import *


class McuToEncode:
    def __init__(self, sub_mcus):
        self._sub_mcus = sub_mcus

    def get_component_ids(self):
        return self._sub_mcus.keys()

    def get_mcus_by_components(self, comp_id):
        return self._sub_mcus[comp_id]


class JpegEncoder:
    def __init__(self, metadata):
        self.metadata = metadata

    def huffman_code(self, comp_id, is_dc, value):
        huff_table = self.metadata.components_to_metadata[comp_id].dc_huffman_table if is_dc else \
           self.metadata.components_to_metadata[comp_id].ac_huffman_table
        huff_lookup = huff_table.get_lookup_table()
        bits_to_write = huff_lookup[value]
        return bits_to_write

    @staticmethod
    def get_bits_from_number(value, num_bits):
        return [((value & (1 << i)) >> i) for i in range(num_bits - 1, -1, -1)]

    @staticmethod
    def table_5_encoding(value_to_encode):
        code = math.ceil(math.log2(math.fabs(value_to_encode) + 1))

        if value_to_encode == 0:
            return code, []

        if value_to_encode > 0:
            additional_bits_value = value_to_encode
        else:
            base_value = 1 - 2 ** code
            additional_bits_value = value_to_encode - base_value

        additional_bits = JpegEncoder.get_bits_from_number(additional_bits_value, code)

        return code, additional_bits

    def encode_dc_value(self, dc_value, dc_prev_values, comp_id, jpeg_bit_writer):
        diff_dc_value = dc_value - dc_prev_values[comp_id]
        dc_prev_values[comp_id] = dc_value

        dc_code, additional_bits = JpegEncoder.table_5_encoding(diff_dc_value)

        dc_code_bits = self.huffman_code(comp_id, True, dc_code)
        jpeg_bit_writer.write_bits(dc_code_bits)
        jpeg_bit_writer.write_bits(additional_bits)

    def encode_ac_values(self, sub_mcu, jpeg_bit_writer, comp_id):
        encoded_idx = 1
        while encoded_idx < 64:
            zero_count = 0
            while encoded_idx < 64:
                x, y = zig_zag_index(encoded_idx)
                if int(sub_mcu[x, y]) == 0:
                    zero_count += 1
                    encoded_idx += 1
                else:
                    break

            if encoded_idx == 64:
                eob_bits = self.huffman_code(comp_id, False, 0)
                jpeg_bit_writer.write_bits(eob_bits)
                return

            while zero_count >= 16:
                zrl_bits = self.huffman_code(comp_id, False, 0xF0)
                jpeg_bit_writer.write_bits(zrl_bits)
                zero_count -= 16

            ac_value = int(sub_mcu[zig_zag_index(encoded_idx)])

            ac_code_size, additional_bits = JpegEncoder.table_5_encoding(ac_value)
            rle_and_size_byte = (zero_count << 4) + ac_code_size
            ac_code_bits = self.huffman_code(comp_id, False, rle_and_size_byte)
            jpeg_bit_writer.write_bits(ac_code_bits)
            jpeg_bit_writer.write_bits(additional_bits)

            encoded_idx += 1

    def encode_sub_mcu(self, sub_mcu, jpeg_bit_writer, dc_prev_values, comp_id):
        dc_value = int(sub_mcu[0, 0])
        self.encode_dc_value(dc_value, dc_prev_values, comp_id, jpeg_bit_writer)
        self.encode_ac_values(sub_mcu, jpeg_bit_writer, comp_id)

    def huffman_encode_mcu(self, mcu_to_encode: McuToEncode, jpeg_bit_writer, dc_prev_values):
        for comp_id in mcu_to_encode.get_component_ids():
            sub_mcu_list = mcu_to_encode.get_mcus_by_components(comp_id)
            for sub_mcu in sub_mcu_list:
                self.encode_sub_mcu(sub_mcu, jpeg_bit_writer, dc_prev_values, comp_id)

    def encode(self, data):
        jpeg_bit_writer = JpegBitWriter()
        dc_prev_values = {comp_id: 0 for comp_id in self.metadata.components_to_metadata.keys()}

        # data is now a collection of mcus
        rst_idx = 0
        for datum_idx in range(len(data)):
            # datum is McuParsedDctComponents
            if datum_idx % 1000 == 0:
                debug_print(datum_idx)
            if self.metadata.restart_interval is not None and datum_idx > 0 and datum_idx % self.metadata.restart_interval == 0:
                self.emit_rst_marker(jpeg_bit_writer, rst_idx)
                rst_idx = (rst_idx + 1) % 8
                dc_prev_values = {comp_id: 0 for comp_id in self.metadata.components_to_metadata.keys()}

            datum = data[datum_idx]
            mcu = McuToEncode(datum.raw_mcus)
            self.huffman_encode_mcu(mcu, jpeg_bit_writer, dc_prev_values)

        debug_print(f"Restart interval: {self.metadata.restart_interval}")
        # jpeg_bit_writer.flush()
        return jpeg_bit_writer.get_all_bytes()

    @staticmethod
    def emit_rst_marker(jpeg_bit_writer, rst_idx):
        jpeg_bit_writer.flush()
        jpeg_bit_writer.write_byte(0xff)
        jpeg_bit_writer.write_byte(0xd0 + rst_idx)
