from marker_writers.i_writer import IWriter


class App14Writer(IWriter):
    def __init__(self):
        super(App14Writer, self).__init__()

    def write(self, jpeg_metadata):
        if jpeg_metadata.app14_data is None:
            return bytearray()
        return bytearray(jpeg_metadata.app14_data)
