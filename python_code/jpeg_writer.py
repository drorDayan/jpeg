from marker_writers.app0_writer import App0Writer
from marker_writers.dht_writer import DhtWriter
from marker_writers.dqt_writer import DqtWriter
from marker_writers.dri_writer import DriWriter
from marker_writers.eoi_marker import EoiWriter
from marker_writers.sof0_writer import Sof0Writer
from marker_writers.soi_writer import SoiWriter
from marker_writers.sos_writer import SosWriter
from marker_writers.app14_writer import App14Writer


class JpegWriter:
    def __init__(self):
        pass

    @staticmethod
    def write(metadata, decoded_data):
        out = bytearray()
        out += SoiWriter().write(metadata)
        out += App0Writer().write(metadata)
        out += App14Writer().write(metadata.color_space)
        out += DriWriter().write(metadata)
        c_out, comp_dqt_tables_indices = DqtWriter().write(metadata)
        out += c_out
        out += Sof0Writer().write((metadata, comp_dqt_tables_indices))
        c_out, ac_tables_indices, dc_tables_indices = DhtWriter().write(metadata)
        out += c_out

        out += SosWriter().write((ac_tables_indices, dc_tables_indices))
        out += decoded_data
        out += EoiWriter().write(metadata)

        path_to_write = 'jpg_from_jpg.jpg'

        with open(path_to_write, 'wb') as f:
            f.write(out)
