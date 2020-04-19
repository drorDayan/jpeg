from marker_parsers.Sof0Parser import Sof0Parser
from marker_parsers.dht_parser import DhtParser
from marker_parsers.dqt_parser import DqtParser
from marker_parsers.eoi_parser import EoiParser
from marker_parsers.sos_parser import SosParser


class Jpeg:
    def __init__(self, jpeg_file_path):
        self._mcu_list = []
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

        self._markers_to_skip = { 0xe1 }

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
                is_continue = parser.parse(self, self._jpg_data[idx_in_file + 4: idx_in_file + 2 + marker_size])
            idx_in_file += (2 + marker_size) # This is including the size and not including the 0xYY marker (so 4-2=2).
