from marker_parsers.i_parser import IParser
from jpeg_common import *


class Sof0Parser(IParser):
    precision_idx = 0
    height_idx = precision_idx + 1
    width_idx = height_idx + 2
    num_of_comp_idx = width_idx + 2
    component_data_idx = num_of_comp_idx + 1
    single_component_data_len = 3

    def parse(self, jpg, raw_marker):
        debug_print("Sof0 parser started")
        print(len(raw_marker))

        assert raw_marker[Sof0Parser.precision_idx] == 8, "precision should be 8"

        height = int.from_bytes(raw_marker[Sof0Parser.height_idx: Sof0Parser.height_idx + 2], byteorder='big')
        width = int.from_bytes(raw_marker[Sof0Parser.width_idx: Sof0Parser.width_idx + 2], byteorder='big')
        jpg.set_height_and_width(height, width)

        num_of_comp = raw_marker[Sof0Parser.num_of_comp_idx]
        assert num_of_comp == 3, "should have 3 components"

        for i in range(num_of_comp):
            comp_id = raw_marker[Sof0Parser.component_data_idx + i*Sof0Parser.single_component_data_len]
            sample_factor = raw_marker[Sof0Parser.component_data_idx + i*Sof0Parser.single_component_data_len + 1]
            # TODO not sure this is correct might be the other way around (horizontal vs vertical)
            horizontal_sample_factor = (sample_factor & 0xf0) >> 4
            vertical_sample_factor = sample_factor & 0x0f
            quantization_table_id = raw_marker[Sof0Parser.component_data_idx + i*Sof0Parser.single_component_data_len+2]
            if not jpg.add_component_quantization_table(comp_id, quantization_table_id):
                return False
            if not jpg.add_component_sample_factors(comp_id, (horizontal_sample_factor, vertical_sample_factor)):
                return False

        debug_print("Sof0 parser ended successfully")
        return True
