import logging
from ..wavep.iwavep import WaveProcessor


_logger = logging.getLogger(__name__)

class OutputWriter:
    VERSION = 1
    def __init__(self) -> None:
        pass

    def save(self, wavp:WaveProcessor, sound_data:list[int], file_path:str):
        raise NotImplementedError()
