class IWriter:
    def __init__(self):
        self._endianess = 'little'

    def write(self, jpeg_metadata):
        raise NotImplementedError()
