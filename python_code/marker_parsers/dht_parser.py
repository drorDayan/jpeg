from python_code.marker_parsers.i_parser import IParser


class DhtParser(IParser):
    def parse(self, raw_chunk):
        print("I'm a DHT parser!")
        return True
