from jpeg_common import ColorSpace
from marker_writers.i_writer import IWriter


class App14Writer(IWriter):
    def __init__(self):
        super(App14Writer, self).__init__()

    def write(self, color_space):
        if color_space in [ColorSpace.RGB, ColorSpace.GreyScale] is None:
            return bytearray()

# TODO
#        NOT ACCURATE. YCBCR for instance can come in 2 forms: either 3 comp without app14 or app14 with tr_Code = 0. What do?

        transform_bit = 1 if color_space
        return bytearray([0xFF, 0xEE, 0x00, 0x0E, 0x41, 0x64, 0x6F, 0x62, 0x65, 0x00, 0x64, 0x00,
                          0x00, 0x00, 0x00, app_14_color_transform])
