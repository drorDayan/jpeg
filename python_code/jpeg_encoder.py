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


        def huffman_encode_mcu(self, mcu_to_encode : McuToEncode, jpeg_bit_writer):
            pass

        def encode(self, data):
            jpeg_bit_writer = JpegBitWriter()

            # data is now a collection of mcus
            for datum in data:
                huffman_encode_mcu(datum, jpeg_bit_writer)
