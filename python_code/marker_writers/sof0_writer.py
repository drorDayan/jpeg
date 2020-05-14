from marker_writers.i_writer import IWriter


class Sof0Writer(IWriter):
    def __init__(self):
        super(Sof0Writer, self).__init__()

    # jpeg_metadata is (JpegDecodeMetadata, comp_dqt_tables_indices)
    def write(self, jpeg_metadata):
        output = bytearray()
        output.append(0xFF)  # SOF0 marker
        output.append(0xC0)
        output.append(0)  # Marker size
        output.append(0)
        output.append(0x08)  # Data precision
        output += bytearray(jpeg_metadata[0].height.to_bytes(2, self._endianess))
        output += bytearray(jpeg_metadata[0].width.to_bytes(2, self._endianess))
        output.append(len(jpeg_metadata[1]))  # num_of_comp

        for comp_id in jpeg_metadata[1].keys():
            output.append(comp_id)
            hsf = jpeg_metadata[0].components_to_metadata[comp_id].horizontal_sample_factor
            vsf = jpeg_metadata[0].components_to_metadata[comp_id].vertical_sample_factor
            sf = vsf + (hsf << 4)
            output.append(sf)
            output.append(jpeg_metadata[1][comp_id])

        real_length = len(output) - 2
        output[2:4] = real_length.to_bytes(2, self._endianess)

        return output

