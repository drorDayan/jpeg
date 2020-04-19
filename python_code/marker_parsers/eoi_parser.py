from python_code.marker_parsers.i_parser import IParser


class EoiParser(IParser):
    def parse(self, jpg, raw_marker):
        print("I'm a EOI parser!")
        jpg._exists_eoi = True
        return True
