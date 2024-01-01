import logging
import wave
import struct
from .iwriter import OutputWriter
from ..wavep.iwavep import WaveProcessor


_logger = logging.getLogger(__name__)

class OutputWriterV1(OutputWriter):
    VERSION = 1
    def __init__(self) -> None:
        super().__init__()
        self._num_channels = 1

    def save(self, wavp:WaveProcessor, sound_data:list[int], file_path:str):
        _logger.debug(f"Saving sound data to : {file_path}")
        frames = b''.join([struct.pack('h', int(s)) for s in sound_data])
        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setparams((wavp.channel_number, wavp.sample_width, wavp.frame_rate, len(sound_data), 'NONE', 'not compressed'))
            wav_file.writeframes(frames)
