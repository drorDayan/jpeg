from python_code.marker_parsers.i_parser import IParser


class SosParser(IParser):
    def parse(self, raw_marker):
        print("I'm a SOS parser. Finishing everything as this one is difficult")
        return False