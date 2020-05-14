class JpegBitWriter:
    def __init__(self):
        self._data = bytearray()
        self._curr_byte = 0x00
        self._bit_idx = 0

    # Writes a bit (0 or 1)
    # DROR: I don't like this double negative, should be called padding and be defaulted to True
    def write_bit(self, bit_to_write, no_padding=False):
        self._curr_byte = self._curr_byte | bit_to_write << (7 - self._bit_idx)
        self._bit_idx += 1
        if self._bit_idx == 8:
            self._data.append(self._curr_byte)
            if self._curr_byte == 0xFF and not no_padding:
                self._data.append(0x00)
            self._curr_byte = 0x00
            self._bit_idx = 0
        return

    # Writes an array of bits (0 or 1 and True or False)
    def write_bits(self, bits_to_write, no_padding=False):
        for b in bits_to_write:
            self.write_bit(1 if b == 1 or b else 0, no_padding)

    # Finish writing the current byte (by adding ones)
    def flush(self):
        while self._bit_idx != 0:
            self.write_bit(1)

    def write_byte(self, byte_to_write, no_padding=True):
        bits_to_write = [((byte_to_write & (1 << i)) >> i) for i in reversed(range(8))]
        # print(f"Writing byte {bits_to_write}")
        self.write_bits(bits_to_write, no_padding)

    def get_all_bytes(self):
        self.flush()
        return self._data
