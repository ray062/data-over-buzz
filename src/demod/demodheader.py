from dataclasses import dataclass
from .demodclass import BlockDataDemod
from .soundprofile import BlockSoundProfile
from .waveutils import WaveUtils
from .bitsutils import BitsUtils



@dataclass
class Header:
    version:int
    checksum:int
    chunk_number:int
    chunk_size:int
    file_length:int

class HeaderDataDemod(BlockDataDemod):
    BLOCK_BITS_NUMBER=377
    BEGINNING_ONES_NUMBER = 100
    BEGINNING_ONES_THRESHOLD = 17
    BEGINNING_VOID_ZERO_NUMBER = 7

    def __init__(self, bsd:BlockSoundProfile, wutils:WaveUtils) -> None:
        super().__init__(bsd, wutils)
        self._header_data = None
        _ = self.header_data

    @property
    def header_data(self):
        if self._header_data is None:
            raw_bits = self._get_raw_bit()
            header_bits = self._get_block_bits(raw_bits)
            version = BitsUtils.bits_to_int(header_bits[:32])
            checksum = BitsUtils.bits_to_int(header_bits[32:32+32])
            chunk_number = BitsUtils.bits_to_int(header_bits[32+32:32+32+32])
            chunk_size = BitsUtils.bits_to_int(header_bits[32+32+32:32+32+32+32])
            file_length = BitsUtils.bits_to_int(header_bits[32+32+32+32:32+32+32+32+64])
            self._header_data = Header(version, checksum, chunk_number, chunk_size, file_length)
        return self._header_data