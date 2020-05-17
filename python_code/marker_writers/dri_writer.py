from marker_writers.i_writer import IWriter


class DriWriter(IWriter):
    def __init__(self):
        super(DriWriter, self).__init__()
        self._DRI_size = 4

    def write(self, jpeg_metadata):
        output = bytearray()
        output.append(0xFF)  # DRI marker
        output.append(0xDD)
        output += bytearray(self._DRI_size.to_bytes(2, self._endianess)) # Marker size
        output += bytearray(jpeg_metadata.restart_interval.to_bytes(2, self._endianess))
        return output
