import logging
import zlib

_logger = logging.getLogger(__name__)

class InputReader:
    # Responsible of IO, compression, encryption
    VERSION = 1
    def __init__(self, input_filepath:str) -> None:
        self._input_filepath = input_filepath
        self._file_stream = None
        self._checksum = None

    def __enter__(self):
        return self

    def open(self):
        if self._file_stream is not None:
            raise Exception("File stream is already opened")
        self._file_stream = open(self._input_filepath, 'rb')
        return self
    
    def read(self, nb_bytes=0):
        if nb_bytes == 0:
            return self._file_stream.read()
        else:
            return self._file_stream.read(nb_bytes)
    
    @property
    def checksum(self):
        if self._checksum is None:
            _logger.debug("Calculating checksum...")
            self.close()
            with self.open() as f:
                self._checksum = zlib.adler32(f.read())
                _logger.debug(f"Checksum:{self._checksum}")
        return self._checksum

    def close(self):
        if self._file_stream is not None:
            self._file_stream.close()
            self._file_stream = None
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()