from dataclasses import dataclass
from bmp_writer import BmpWriter
from jpeg_common import *
from jpeg_decoder import JpegDecoder
from marker_parsers.app14_parser import App14Parser
from marker_parsers.dht_parser import DhtParser, HuffTable
from marker_parsers.dqt_parser import DqtParser
from marker_parsers.dri_parser import DriParser
from marker_parsers.eoi_parser import EoiParser
from marker_parsers.sof0_parser import Sof0Parser
from marker_parsers.sos_parser import SosParser


# This class is a combination of a Jpeg metadata builder and the main jpeg decoding functionality (Fix in the real code)
def compute_color_space(num_components, app14_color_transform):
    if num_components == 1:
        return ColorSpace.GreyScale

    if num_components == 3:
        if app14_color_transform is None or app14_color_transform == 0:
            return ColorSpace.RGB
        else:
            assert (app14_color_transform == 1)
            return ColorSpace.YCbCr

    else:
        assert (num_components == 4)
        if app14_color_transform is None or app14_color_transform == 0:
            return ColorSpace.CMYK
        else:
            assert (app14_color_transform == 2)
            return ColorSpace.YCCK


class Jpeg:
    def __init__(self, jpeg_file_path):
        self._ac_huffman_tables = {}
        self._dc_huffman_tables = {}
        self._quantization_tables = {}
        self._component_id_to_quantization_table_id = {}
        self._component_id_to_huffman_tables_ids = {}
        self._component_id_to_sample_factors = {}
        self._exists_eoi = False

        self.app14_color_transform = None
        self.restart_interval = None
        self.height = None
        self.width = None

        self.jpeg_decode_metadata = None

        jpeg_file = open(jpeg_file_path, 'rb')
        self._jpg_data = jpeg_file.read()
        jpeg_file.close()

        self._marker_parsers = \
            {
                0xc4: DhtParser,
                0xda: SosParser,
                0xdb: DqtParser,
                0xc0: Sof0Parser,
                0xd9: EoiParser,
                0xdd: DriParser,
                0xee: App14Parser
            }
        '''
        .jpg_ignore:
        DRI
        APPn, n>=1
        '''
        self._markers_to_skip = {i for i in range(0xe0, 0xe0 + 14)} | {0xfe}

    def parse(self):
        info_print("Started parsing!")
        # DROR what are this consts? and are they full i.e. exif and jfif
        if self._jpg_data[0] != 0xff or self._jpg_data[1] != 0xd8:
            raise Exception("Illegal SOI")

        idx_in_file = 2

        image_matrix = None
        actual_width = actual_height = None

        while idx_in_file < len(self._jpg_data):
            is_continue = True
            marker = self._jpg_data[idx_in_file:idx_in_file + 2]
            marker_size = int.from_bytes(self._jpg_data[idx_in_file + 2: idx_in_file + 4], byteorder='big')
            marker_type = marker[1]

            if marker_type not in self._markers_to_skip:
                if marker_type not in self._marker_parsers.keys():
                    raise Exception(f"no marker of type {hex(marker_type)} implemented!")

                parser = self._marker_parsers[marker_type]()
                start_idx = idx_in_file + 4
                is_continue = parser.parse(self, self._jpg_data[start_idx: start_idx + marker_size - 2])
            idx_in_file += (2 + marker_size)  # This is including the size and not including the 0xYY marker (so 4-2=2).

            if not is_continue:
                info_print("SOS read. Starting decoding")
                self.finalize_metadata()
                info_print("Finished finalizing metadata!")

                bytes_read, image, actual_width, actual_height = self.decode_raw_data(idx_in_file)

                # TODO move this after debug to after the while loop
                bmp_writer = BmpWriter()
                bmp_writer.write_from_rgb(image, width=actual_width, height=actual_height)
                idx_in_file += bytes_read
                image_matrix = image
                info_print("Picture decoded!")

        info_print("Parsing completed!")
        info_print("Beginning BMP creation!")
        if image_matrix is None or actual_height is None or actual_width is None:
            raise Exception("Error in retrieving image data")
        #    bmp_writer = BmpWriter()
        assert self._exists_eoi
        #    bmp_writer.write_from_rgb(image_matrix, width=actual_width, height=actual_height)
        info_print("Finished creating BMP!")

    def decode_raw_data(self, start_idx):
        decoder = JpegDecoder(self._jpg_data[start_idx:], self.jpeg_decode_metadata)
        new_idx, image, actual_width, actual_height = decoder.decode()
        return new_idx, image, actual_width, actual_height

    def add_huffman_table(self, huff_table):
        table_id = huff_table.get_table_id()
        is_dc = huff_table.get_is_dc()
        huffman_tables = self._dc_huffman_tables if is_dc else self._ac_huffman_tables
        if table_id in huffman_tables.keys():
            raise Exception("error huffman table with this id exists")

        huffman_tables[table_id] = huff_table

    def add_quantization_table(self, table_id, quantization_table_to_add):
        if table_id in self._quantization_tables:
            raise Exception("error quantization table with this id exists")
        self._quantization_tables[table_id] = quantization_table_to_add
        return True

    def add_component_quantization_table(self, component_id, quantization_table_id):
        if component_id in self._component_id_to_quantization_table_id:
            raise Exception("error this component_id has a quantization_table assigned to him")
        self._component_id_to_quantization_table_id[component_id] = quantization_table_id
        return True

    def add_component_sample_factors(self, component_id, sample_factors):
        if component_id in self._component_id_to_sample_factors:
            raise Exception("error this component_id has a sample_factors assigned to him")
        self._component_id_to_sample_factors[component_id] = sample_factors
        return True

    def add_component_huffman_table(self, comp_id, ac_table, dc_table):
        if comp_id in self._component_id_to_huffman_tables_ids.keys():
            raise Exception("error component ID already has huffman tables assigned to it")
        self._component_id_to_huffman_tables_ids[comp_id] = (ac_table, dc_table)

    @dataclass
    class ComponentMetadata:
        ac_huffman_table: HuffTable
        dc_huffman_table: HuffTable
        quantization_table: []
        horizontal_sample_factor: int
        vertical_sample_factor: int
        number_of_instances_in_mcu: int

    @dataclass
    class JpegDecodeMetadata:
        restart_interval: int
        horiz_pixels_in_mcu: int
        vert_pixels_in_mcu: int
        height: int
        width: int
        components_to_metadata: {}
        # app14_color_tranform: None
        color_space: ColorSpace

    '''This function collects all data related to specific components into one CONVENIENT data structure
    we need to do this because the metadata of each component is the indexes of tables
    and the tables might be defined afterwards'''

    def finalize_metadata(self):
        components_to_metadata = {}

        for comp_id in self._component_id_to_quantization_table_id.keys():
            ac_t = self._ac_huffman_tables[self._component_id_to_huffman_tables_ids[comp_id][0]]
            dc_t = self._dc_huffman_tables[self._component_id_to_huffman_tables_ids[comp_id][1]]
            q_t = self._quantization_tables[self._component_id_to_quantization_table_id[comp_id]]
            horizontal_sample_factor, vertical_sample_factor = self._component_id_to_sample_factors[comp_id]
            components_to_metadata[comp_id] = Jpeg.ComponentMetadata(
                ac_t, dc_t, q_t, horizontal_sample_factor, vertical_sample_factor, 0)

        min_vertical_sample_factor = min([comp.vertical_sample_factor for comp in components_to_metadata.values()])
        max_vertical_sample_factor = max([comp.vertical_sample_factor for comp in components_to_metadata.values()])
        min_horizontal_sample_factor = min([comp.horizontal_sample_factor for comp in components_to_metadata.values()])
        max_horizontal_sample_factor = max([comp.horizontal_sample_factor for comp in components_to_metadata.values()])

        # We assume we only have 2 options for sample_factor, Ys option which is the higher one and the smaller one for
        #  both Cb and Cr
        assert max_vertical_sample_factor == components_to_metadata[Y_COMP_ID].vertical_sample_factor
        assert max_horizontal_sample_factor == components_to_metadata[Y_COMP_ID].horizontal_sample_factor

        for comp_id in self._component_id_to_quantization_table_id.keys():
            if comp_id == Y_COMP_ID:
                continue
            assert min_vertical_sample_factor == components_to_metadata[comp_id].vertical_sample_factor
            assert min_horizontal_sample_factor == components_to_metadata[comp_id].horizontal_sample_factor

        for comp in components_to_metadata.values():
            comp.number_of_instances_in_mcu = \
                comp.horizontal_sample_factor // min_horizontal_sample_factor \
                * comp.vertical_sample_factor // min_vertical_sample_factor

        assert max_horizontal_sample_factor % min_horizontal_sample_factor == 0
        assert max_vertical_sample_factor % min_vertical_sample_factor == 0

        assert min_horizontal_sample_factor == 1 and min_vertical_sample_factor == 1, \
            "Learn about min sampling factors...."
        horiz_pixels_in_mcu = 8 * max_horizontal_sample_factor // min_horizontal_sample_factor
        vert_pixels_in_mcu = 8 * max_vertical_sample_factor // min_vertical_sample_factor

        debug_print(
            f"Parsed MCU size: {horiz_pixels_in_mcu} over {vert_pixels_in_mcu} pixels")

        num_components = len(self._component_id_to_quantization_table_id.keys())
        color_space = compute_color_space(num_components, self.app14_color_transform)
        self.jpeg_decode_metadata = Jpeg.JpegDecodeMetadata(self.restart_interval, horiz_pixels_in_mcu,
                                                            vert_pixels_in_mcu, self.height,
                                                            self.width, components_to_metadata,
                                                            color_space)
