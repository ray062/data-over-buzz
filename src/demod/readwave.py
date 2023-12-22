import logging
import wave

_logger = logging.getLogger(__name__)

class WaveReader:
    VERSION=1

    def __init__(self, wave_file_path) -> None:
        self._read(wave_file_path)

    def _read(self, wave_file_path:str):
        channel = 0
        with wave.open(wave_file_path, 'rb') as wave_file:
            self._num_channels = wave_file.getnchannels()
            self._sample_width = wave_file.getsampwidth()
            self._frame_rate = wave_file.getframerate()
            self._num_frames = wave_file.getnframes()
            raw_data = wave_file.readframes(self._num_frames)
            wave_file.close()
        self._data = []
        for i in range(self._num_frames*self._num_channels):
            if i % self._num_channels == channel:
                start = i * self._sample_width
                end = start + self._sample_width
                self._data.append(int.from_bytes(raw_data[start:end], byteorder='little', signed=True))

    @property
    def data(self)->list[int]:
        return self._data
    
    @property
    def frame_rate(self)->int:
        return self._frame_rate
    
    @property
    def sample_width(self)->int:
        return self._sample_width
    
    @property
    def channel_number(self)->int:
        return self._num_channels
    
    @property
    def num_frames(self)->int:
        return self._num_frames