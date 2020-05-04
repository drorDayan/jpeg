from jpeg_common import debug_print
from marker_parsers.i_parser import IParser


class DriParser(IParser):
    def parse(self, jpg, raw_marker):
        debug_print("DRI parser started")
        if len(raw_marker) != 2:
            raise Exception("Invalid size of DRI marker")
        rst_interval = int.from_bytes(raw_marker[0: 2], byteorder='big')
        jpg.restart_interval = rst_interval
        debug_print("DRI parser ended successfully")
        return True
