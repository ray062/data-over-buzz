from .demodclass import BlockDataDemod
from .soundprofile import BlockSoundProfile
from .waveutils import WaveUtils
from .demodmeta import MetaData
from .demodheader import Header


class FileDataDemod(BlockDataDemod):
    BEGINNING_ONES_NUMBER = 3
    BEGINNING_ONES_THRESHOLD = 1
    BEGINNING_VOID_ZERO_NUMBER = 1

    def __init__(self, bsd:BlockSoundProfile, wutils:WaveUtils, meta:MetaData, header:Header) -> None:
        super().__init__(bsd, wutils)
        self._header = header
        self._meta = meta

    def demod_file_data(self)->str:
        file_bits = ""
        remaining_file_length = self._header.file_length
        for cn in range(self._header.chunk_number):
            raw_bits = self._get_raw_bit()
            chunk_data = self._get_block_bits(raw_bits)
            self._bsp.sound_data = self.remaining_sound_data
            
            if remaining_file_length >= self._header.chunk_size:
                file_bits = f"{file_bits}{chunk_data}"
                remaining_file_length = remaining_file_length - self._header.chunk_size
            else:
                file_bits = f"{file_bits}{chunk_data[:remaining_file_length]}"
                remaining_file_length = 0
                break
        return file_bits
    
    