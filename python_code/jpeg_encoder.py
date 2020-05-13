import math

from jpeg_bit_writer import JpegBitWriter


class JpegEncoder:
    def __init__(self, metadata):
        self.metadata = metadata

        class McuToEncode:
            def __init__(self, sub_mcus):
                self._sub_mcus = sub_mcus

            def get_component_ids(self):
                return self._sub_mcus.keys()

            def get_mcus_by_components(self, comp_id):
                return self._sub_mcus[comp_id]


        def encode_dc_value(self, dc_value, dc_prev_values, comp_id):
            diff_dc_value = dc_value - dc_prev_values[comp_id]

            dc_code = math.ceil(math.log2(math.fabs(diff_dc_value) + 1))

            additional_bits = []
            if diff_dc_value > 0:
                return 9
            elif diff_dc_value < 0:
                return 8



        def encode_sub_mcu(self, sub_mcu, jpeg_bit_writer, dc_prev_values, comp_id):
            dc_value = sub_mcu[0,0]
            self.encode_dc_value(dc_value, dc_prev_values, comp_id)

        def huffman_encode_mcu(self, mcu_to_encode : McuToEncode, jpeg_bit_writer):
            dc_prev_values = {comp_id : 0 for comp_id in mcu_to_encode.get_component_ids()}
            for comp_id in mcu_to_encode.get_component_ids():
                sub_mcu_list = mcu_to_encode.get_mcus_by_components(comp_id)
                for sub_mcu in sub_mcu_list:
                    self.encode_sub_mcu(sub_mcu, jpeg_bit_writer, dc_prev_values, comp_id)


        def encode(self, data):
            jpeg_bit_writer = JpegBitWriter()

            # data is now a collection of mcus
            for datum in data:
                self.huffman_encode_mcu(datum, jpeg_bit_writer)





