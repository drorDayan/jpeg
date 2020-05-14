
def bit_getter(bit_idx, byte):
    return (byte & (1 << (7 - bit_idx))) > 0


class JpegBitReader:
    BYTE_SIZE = 8

    def __init__(self, src_bytes):
        assert (len(src_bytes) > 0)
        self._bytes = src_bytes
        self._input_len = len(self._bytes)
        self._byte_idx = 0
        self._bit_idx = 0
        self._last_byte_is_FF = src_bytes[0] == 0xFF

    def get_byte_location(self):
        return self._byte_idx if self._bit_idx == 0 else self._byte_idx + 1

    def at_end(self):
        return self._byte_idx >= self._input_len

    def get_bits_as_bool_list(self, num_bits_to_read):
        bits_to_return = []

        while len(bits_to_return) < num_bits_to_read and not self.at_end():
            next_bit = bit_getter(self._bit_idx, self._bytes[self._byte_idx])
            bits_to_return.append(next_bit)
            self._bit_idx += 1

            if self._bit_idx == self.BYTE_SIZE:
                self._bit_idx = 0
                self._byte_idx += 1

                if not self.at_end():
                    if self._bytes[self._byte_idx] == 0xFF:
                        self._last_byte_is_FF = True
                    elif self._last_byte_is_FF:
                        if self._bytes[self._byte_idx] == 0:
                            # debug_print("FF00 Happened!")
                            self._byte_idx += 1
                        else:
                            assert 0xd0 <= self._bytes[self._byte_idx] <= 0xd7
                        self._last_byte_is_FF = self._bytes[self._byte_idx] == 0xFF

        return bits_to_return

    def read_bits_as_int(self, num_bits):
        res_bits = self.get_bits_as_bool_list(num_bits)
        return sum([2 ** (len(res_bits) - 1 - i) for i in range(len(res_bits)) if res_bits[i]])

    def align(self):
        read_curr = self._bit_idx != 0
        if read_curr:
            res = self.get_bits_as_bool_list(self.BYTE_SIZE - self._bit_idx)
            if not all(res):
                raise Exception("Alignment is wrong.")
