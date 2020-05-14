from i_writer import IWriter


class EoiWriter(IWriter):
    def __init__(self):
        pass

    def write(self, jpeg_metadata):
        return [0xFF, 0xD9]