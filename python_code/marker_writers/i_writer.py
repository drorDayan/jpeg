class IWriter:
    def __init__(self):
        self._endianess = 'big'

    def write(self, jpeg_metadata):
        raise NotImplementedError()
