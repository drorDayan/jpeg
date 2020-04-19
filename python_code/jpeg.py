from marker_parsers.sof0_parser import Sof0Parser
from marker_parsers.dht_parser import DhtParser
from marker_parsers.dqt_parser import DqtParser
from marker_parsers.eoi_parser import EoiParser
from marker_parsers.sos_parser import SosParser


class Jpeg:
    def __init__(self, jpeg_file_path):
        self._mcu_list = []
        self._huffman_tables = {}
        self._quantization_tables = {}
        self._height = None
        self._width = None
        self._component_id_to_quantization_table_id = {}

        self._component_id_to_huffman_tables_ids = {}
        self._num_components = None

        self._component_id_to_sample_factors = {}

        self._exists_eoi = False

        jpeg_file = open(jpeg_file_path, 'rb')
        self._jpg_data = jpeg_file.read()
        jpeg_file.close()

        self._marker_parsers = \
            {
                0xc4: DhtParser,
                0xda: SosParser,
                0xdb: DqtParser,
                0xc0: Sof0Parser,
                0xd9: EoiParser
            }

        '''
        .jpg_ignore:
        DRI
        APPn, n>=1
        '''
        self._markers_to_skip = { i for i in range(0xe1, 0xef+1) }  | {0xdd}

    def parse(self):
        print("Started parsing!")
        if self._jpg_data[0] != 0xff or self._jpg_data[1] != 0xd8:
            raise Exception("Illegal SOI")

        idx_in_file = 2
        is_continue = True
        while idx_in_file < len(self._jpg_data) and is_continue:
            marker = self._jpg_data[idx_in_file:idx_in_file + 2]
            marker_size = int.from_bytes(self._jpg_data[idx_in_file + 2: idx_in_file + 4], byteorder='big')
            print(f"idx={idx_in_file}")
            print(f"Marker size: {marker_size}")

            marker_type = marker[1]
            if marker_type not in self._markers_to_skip:
                if marker_type not in self._marker_parsers.keys():
                    raise Exception(f"no marker of type {hex(marker_type)} implemented!")

                parser = self._marker_parsers[marker_type]()
                start_idx = idx_in_file + 4
                is_continue = parser.parse(self, self._jpg_data[start_idx: start_idx + marker_size - 2])
            idx_in_file += (2 + marker_size) # This is including the size and not including the 0xYY marker (so 4-2=2).

        print("Parsing completed!")

    def add_huffman_table(self, huff_table):
        table_id = huff_table.get_table_id()
        is_dc = huff_table.get_is_dc()
        if table_id in self._huffman_tables.keys():
            raise Exception("error quantization table with this id exists")

        self._huffman_tables[(table_id, is_dc)] = huff_table

    def add_quantization_table(self, table_id, quantization_table_to_add):
        if table_id in self._quantization_tables:
            print("error quantization table with this id exists")
            return False
        self._quantization_tables[table_id] = quantization_table_to_add
        return True

    def set_height_and_width(self, height, width):
        self._height = height
        self._width = width

    def add_component_quantization_table(self, component_id, quantization_table_id):
        if component_id in self._component_id_to_quantization_table_id:
            print("error this component_id has a quantization_table assigned to him")
            return False
        self._component_id_to_quantization_table_id[component_id] = quantization_table_id
        return True

    def add_component_sample_factors(self, component_id, sample_factors):
        if component_id in self._component_id_to_sample_factors:
            print("error this component_id has a sample_factors assigned to him")
            return False
        self._component_id_to_sample_factors[component_id] = sample_factors
        return True
