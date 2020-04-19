from python_code.marker_parsers.i_parser import IParser


class Sof0Parser(IParser):
    def parse(self, jpg, raw_marker):
        print("I'm a SOF0 parser!")
        return True
