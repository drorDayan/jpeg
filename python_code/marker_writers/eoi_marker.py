from marker_writers.i_writer import IWriter


class EoiWriter(IWriter):
    def __init__(self):
        super(EoiWriter, self).__init__()

    def write(self, jpeg_metadata):
        return [0xFF, 0xD9]
