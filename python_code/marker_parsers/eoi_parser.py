from marker_parsers.i_parser import IParser


class EoiParser(IParser):
    def parse(self, jpg, raw_marker):
        print("EOI marker met!")
        jpg._exists_eoi = True
        return True
