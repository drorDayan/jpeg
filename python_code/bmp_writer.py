import numpy

from jpeg_common import debug_print


class BmpWriter:
    def __init__(self):
        self._endianess = 'little'

        '''
        BMP_INFO_HEADER
        '''
        self._info_header_size = 40
        self._num_planes = 1
        self._bits_per_pixel = 24
        self._compression = 0
        self._image_size = 0  # OK as compression = 0
        self._pixels_per_meters_x = self._pixels_per_meters_y = 0
        self._num_colors = 0  # 2 ** bits per pixel is used
        self._num_important_colors = 0

        '''
        BMP_HEADER
        '''
        self._file_size = 0
        self._reserved = 0
        self._pixel_data_offset = 40 + 14

    # input is dict {i,j -> {color_comp -> np.matrix(8,8), color_comp in range(number_of_components)]}
    def write_from_rgb(self, rgb_mat, width, height, path_to_write='bmp_from_jpg.bmp'):
        bytes_to_write = self.get_bytes_to_write(rgb_mat, width, height)

        with open(path_to_write, 'wb') as f:
            f.write(bytes_to_write)

        print('BMP generated!')

    def get_bytes_to_write(self, rgb_mat, width, height):
        to_write = bytearray(b"")
        bitmap_header = self._generate_bitmap_header()
        bitmap_info_header = self.generate_bitmap_info_header(width, height)
        color_palatte = bytearray(b"")  # No color palatte as we use 24bits for each pixel
        actual_image_data = self._generate_image_data(rgb_mat, width, height)

        to_write += bitmap_header
        to_write += bitmap_info_header
        to_write += color_palatte
        to_write += actual_image_data

        return to_write

    def generate_bitmap_info_header(self, width, height):
        to_write = bytearray()

        to_write += bytearray(self._info_header_size.to_bytes(4, self._endianess))
        to_write += bytearray(width.to_bytes(4, self._endianess))
        to_write += bytearray(height.to_bytes(4, self._endianess))
        to_write += bytearray(self._num_planes.to_bytes(2, self._endianess))
        to_write += bytearray(self._bits_per_pixel.to_bytes(2, self._endianess))
        to_write += bytearray(self._compression.to_bytes(4, self._endianess))
        to_write += bytearray(self._image_size.to_bytes(4, self._endianess))
        to_write += bytearray(self._pixels_per_meters_x.to_bytes(4, self._endianess))
        to_write += bytearray(self._pixels_per_meters_y.to_bytes(4, self._endianess))
        to_write += bytearray(self._num_colors.to_bytes(4, self._endianess))
        to_write += bytearray(self._num_important_colors.to_bytes(4, self._endianess))

        return to_write

    def _generate_bitmap_header(self):
        to_write = bytearray()
        to_write.append(0x42)  # B
        to_write.append(0x4D)  # M

        to_write += bytearray(self._file_size.to_bytes(4, self._endianess))
        to_write += bytearray(self._reserved.to_bytes(4, self._endianess))
        to_write += bytearray(self._pixel_data_offset.to_bytes(4, self._endianess))

        return to_write

    @staticmethod
    def keep_in_byte(value):
        if value > 255:
            value = 255
        elif value < 0:
            value = 0
        return value

    @staticmethod
    def _generate_image_data(rgb_mat, width, height):
        padding_for_each_row = (4 - ((width * 3) % 4)) % 4
        padding = bytearray(padding_for_each_row)

        to_write = bytearray()

        # To run on the row in a backwards manner that how bmp likes it
        for row_idx in reversed(range(height)):
            debug_print(f"Printing row {row_idx} to BMP")
            for col_idx in range(width):
                # To do BGR instead of RGB (that how BMP works)
                for comp in reversed(range(3)):
                    try:
                        value = BmpWriter.keep_in_byte(rgb_mat[row_idx, col_idx, comp])
                        to_write.append(int(value))
                    except:
                        print(f"Value in {row_idx, col_idx, comp}: {rgb_mat[row_idx, col_idx, comp]} is out of range!")
                        return bytearray()

            to_write += padding
        return to_write
