from marker_writers.i_writer import IWriter


class App0Writer(IWriter):
    def __init__(self):
        super(App0Writer, self).__init__()

    def write(self, jpeg_metadata):
        return [0xFF, 0xE0, 0, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x01, 0x00,
                0x01, 0x00, 0x01, 0x00, 0x00]

