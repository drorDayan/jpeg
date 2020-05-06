from jpeg_common import *
from marker_parsers.i_parser import IParser


class SosParser(IParser):
    def parse(self, jpg, raw_marker):
        info_print("Sos parser started")
        if raw_marker[0] < 1 or raw_marker[0] > 4:
            raise Exception("Illegal number of components in SOS")
        num_components = raw_marker[0]
        assert num_components == number_of_components, f"Num components must be {number_of_components}"

        idx = 1
        for comp_id in range(num_components):
            comp_id = raw_marker[idx]
            ac_table = raw_marker[idx + 1] & 0x0F
            dc_table = (raw_marker[idx + 1] & 0xF0) >> 4

            jpg.add_component_huffman_table(comp_id, ac_table, dc_table)
            idx += 2

        assert len(raw_marker) - 3 == idx, "File SOS must contain 3 ignore bytes"
        info_print("Sos parser ended successfully")
        return False
