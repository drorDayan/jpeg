from jpeg_common import info_print
from marker_parsers.i_parser import IParser


class App14Parser(IParser):
    def parse(self, jpg, raw_marker):
        info_print("App14 parser started")
        assert(len(raw_marker) == 12)
        jpg.app14_color_transform = raw_marker[-1]
        info_print("App14 parser ended successfully")

        return True
