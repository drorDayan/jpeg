from marker_writers.i_writer import IWriter


class SosWriter(IWriter):
    def __init__(self):
        super(SosWriter, self).__init__()

    # jpeg_metadata is (comp_ac_tables_indices, comp_dc_tables_indices)
    def write(self, jpeg_metadata):
        output = bytearray()
        output.append(0xFF)  # SOF0 marker
        output.append(0xDA)
        output.append(0)  # Marker size
        output.append(0)
        output.append(len(jpeg_metadata[1]))  # num_of_comp

        for comp_id in jpeg_metadata[1].keys():
            output.append(comp_id)
            ac_t_idx = jpeg_metadata[0][comp_id]
            dc_t_idx = jpeg_metadata[1][comp_id]
            huff_t_idx = ac_t_idx + (dc_t_idx << 4)
            output.append(huff_t_idx)

        output.append(0)
        output.append(63)
        output.append(0)

        real_length = len(output) - 2
        output[2:4] = real_length.to_bytes(2, self._endianess)

        return output

