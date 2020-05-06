import numpy

from marker_parsers.i_parser import IParser
from jpeg_common import *


class DqtParser(IParser):
    def parse(self, jpg, raw_marker):
        info_print("DQT parser started")
        idx = 0
        while idx < len(raw_marker):
            # bits 4-7 are precision, 0 is 8 bits, otherwise 16 bit
            precision = raw_marker[idx] & 0xf0
            if precision == 0:
                table_length = 64
            else:
                raise Exception("this is a new one, handle this please")
            table_id = raw_marker[idx] & 0x0f
            if table_id > 3:
                raise Exception("illegal table_id")
            idx += 1

            new_table = numpy.zeros((8, 8))
            for i in range(table_length):
                new_table[i // 8, i % 8] = raw_marker[idx+i]
            idx += table_length
            jpg.add_quantization_table(table_id, new_table)
        info_print("DQT parser ended successfully")
        return True
