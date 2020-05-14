from marker_writers.i_writer import IWriter


class SoiWriter(IWriter):
    def __init__(self):
        super(SoiWriter, self).__init__()

    def write(self, jpeg_metadata):
        return bytearray([0xFF, 0xD8])
