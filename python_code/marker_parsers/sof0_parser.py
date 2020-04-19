from marker_parsers.i_parser import IParser
from jpeg_common import *


class Sof0Parser(IParser):
    precision_idx = 0
    height_idx = precision_idx + 1
    width_idx = height_idx + 2

    def parse(self, jpg, raw_marker):
        debug_print("Sof0 parser started")
        print(len(raw_marker))
        assert raw_marker[Sof0Parser.precision_idx] == 8, "precision should be 8"
        height = int.from_bytes(raw_marker[Sof0Parser.height_idx: Sof0Parser.height_idx + 2], byteorder='big')
        width = int.from_bytes(raw_marker[Sof0Parser.width_idx: Sof0Parser.width_idx + 2], byteorder='big')

        jpg.set_height_and_width(height, width)

        debug_print("Sof0 parser ended successfully")
        return True
