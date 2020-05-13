class JpegBitWriter:
    def __init__(self):
        self._bit_idx = 0
        self._last_byte_is_ff = False
        self._data_place = bytearray()
        self._byte_buffer = 0x00

    def write_bit(self):
        pass

