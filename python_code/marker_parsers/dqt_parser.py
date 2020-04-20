from marker_parsers.i_parser import IParser
from jpeg_common import *


class DqtParser(IParser):
    def parse(self, jpg, raw_marker):
        debug_print("DQT parser started")
        idx = 0
        while idx < len(raw_marker):
            table_length = raw_marker[idx] & 0xf0
            if table_length == 0:
                table_length = 64  # I'm not sure about this part. Shouldn't it be 8 bits so one byte?
            else:
                print("this is a new one, handle this please") # Why? it means percision is 16, doesnt it?
            table_id = raw_marker[idx] & 0x0f  # Can only be a value from 0 to 3?
            idx += 1
            new_table = list(raw_marker[idx:idx+table_length]) # The bits/bytes seems wrong to me.
            idx += table_length
            if not jpg.add_quantization_table(table_id, new_table):
                return False
        debug_print("DQT parser ended successfully")
        return True
