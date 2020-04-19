from marker_parsers.i_parser import IParser
from jpeg_common import *


class DqtParser(IParser):
    def parse(self, jpg, raw_marker):
        debug_print("DQT parser started")
        idx = 0
        while idx < len(raw_marker):
            table_length = raw_marker[idx] & 0xf0
            if table_length == 0:
                table_length = 64
            else:
                print("this is a new one, handle this please")
            table_id = raw_marker[idx] & 0x0f
            idx += 1
            new_table = list(raw_marker[idx:idx+table_length])
            idx += table_length
            if not jpg.add_quantization_table(table_id, new_table):
                return False
        debug_print("DQT parser ended successfully")
        return True
