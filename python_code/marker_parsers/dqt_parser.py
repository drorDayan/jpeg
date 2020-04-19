from python_code.marker_parsers.i_parser import IParser


class DqtParser(IParser):
    def parse(self, raw_marker):
        print("I'm a DQT parser")
        return True
