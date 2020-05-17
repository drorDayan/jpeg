from jpeg_common import ColorSpace
from marker_writers.i_writer import IWriter


class App14Writer(IWriter):
    def __init__(self):
        super(App14Writer, self).__init__()

    def write(self, app14_metadata):
        color_space, num_of_comp = app14_metadata[0], app14_metadata[1]
        app_14_color_transform = 0xff
        if color_space is ColorSpace.GreyScale:
            assert num_of_comp == 1
            return bytearray()
        elif color_space is ColorSpace.RGB:
            assert num_of_comp == 3
            app_14_color_transform = 0x00
        elif color_space is ColorSpace.YCbCr:
            assert num_of_comp == 3
            return bytearray()
        elif color_space is ColorSpace.CMYK:
            assert num_of_comp == 4
            app_14_color_transform = 0x00
        elif color_space is ColorSpace.YCCK:
            assert num_of_comp == 4
            app_14_color_transform = 0x02
        assert app_14_color_transform != 0xff, "This means we didn't handle app 14 correctly"
        return bytearray([0xFF, 0xEE, 0x00, 0x0E, 0x41, 0x64, 0x6F, 0x62, 0x65, 0x00, 0x64, 0x00,
                          0x00, 0x00, 0x00, app_14_color_transform])
