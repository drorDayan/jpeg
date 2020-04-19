from marker_parsers.i_parser import IParser


class DqtParser(IParser):
    def parse(self, jpg, raw_marker):
        print("I'm a DQT parser")
        return True
