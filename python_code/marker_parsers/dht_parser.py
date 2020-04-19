from marker_parsers.i_parser import IParser


class DhtParser(IParser):
    def parse(self, jpg, raw_chunk):
        print("I'm a DHT parser!")
        return True
