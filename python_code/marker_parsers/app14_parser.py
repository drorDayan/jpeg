from jpeg_common import info_print
from marker_parsers.i_parser import IParser


class App14Parser(IParser):
    def parse(self, jpg, raw_marker):
        info_print("App14 parser started")
        data = b'\xFF \xee \x00 \x0e'
        data += raw_marker
        jpg.add_app14(data)
        info_print("App14 parser ended successfully")

        return True
