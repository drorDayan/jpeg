class JpegBitWriter:
    def __init__(self):
        self._last_byte_is_ff = False  # This is useless I will simply check when I write a byte
        self._data = bytearray()
        self._curr_byte = 0x00
        self._bit_idx = 0

    # Writes a bit (0 or 1)
    def write_bit(self, bit_to_write):
        self._curr_byte = self._curr_byte | bit_to_write << (7 - self._bit_idx)
        self._bit_idx += 1
        if self._bit_idx == 8:
            self._data.append(self._curr_byte)
            if self._curr_byte == 0xFF:
                self._data.append(0x00)
            self._curr_byte = 0x00
            self._bit_idx = 0
        return

    # Writes an array of bits (0 or 1 and True or False)
    def write_bits(self, bits_to_write):
        for b in bits_to_write:
            self.write_bit(1 if b == 1 or b else 0)

    # Finish writing the current byte (by adding ones)
    def flush(self):
        while self._bit_idx != 0:
            self.write_bit(1)

    def write_byte(self, byte_to_write):
        bits_to_write = [(byte_to_write & (1 << 7-i)) >> (7-i) for i in range(8)]
        self.write_bits(bits_to_write)
    def poop_all(self):
        return self._data
