def bit_getter(i):
    return lambda byte: ((byte & (1 << (7-i))) > 0)


class JpegBitReader:
    BYTE_SIZE = 8
    bit_getters = {i: bit_getter(i) for i in range(BYTE_SIZE)}

    def __init__(self, src_bytes):
        assert (len(src_bytes) > 0)
        self._bytes = src_bytes
        self._byte_idx = 0
        self._bit_idx = 0
        self._last_byte_is_FF = src_bytes[0] == 0xFF

    def at_end(self):
        return self._byte_idx >= len(self._bytes)

    def get_bits_as_bool_list(self, num_bits_to_read):
        bits_to_return = []

        while len(bits_to_return) < num_bits_to_read and not self.at_end():
            next_bit = self.bit_getters[self._bit_idx](self._bytes[self._byte_idx])
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
                            print("FF00 Happened!")
                            self._byte_idx += 1
                        else:
                            print(f"BAD MARKER: FF{hex(self._bytes[self._byte_idx])} ")
                           # raise Exception("IEEE MARKER HERE")
                        self._last_byte_is_FF = False

        return bits_to_return

    def read_bits_as_int(self, num_bits):
        res_bits = self.get_bits_as_bool_list(num_bits)
        return sum([2**i for i in range(len(res_bits)) if res_bits[i]])
