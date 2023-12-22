from dataclasses import dataclass
from .waveutils import WaveUtils
from .bitsutils import BitsUtils
from .soundprofile import BlockSoundProfile
from .demodclass import BlockDataDemod




@dataclass
class MetaData:
    reserved:int
    frequency:int
    reader_version:int
    bitp_version:int
    wave_version:int

    @classmethod
    def compatible_check(cls, meta)->bool:
        if meta.reader_version != 1:
            return False
        if meta.bitp_version != 1:
            return False
        if meta.wave_version != 1:
            return False
        return True

class MetaDataDemod(BlockDataDemod):
    BLOCK_BITS_NUMBER=120
    META_FREQ = 1000
    BEGINNING_ONES_NUMBER = 20
    BEGINNING_ONES_THRESHOLD = 7
    BEGINNING_VOID_ZERO_NUMBER = 1

    def __init__(self, bsd:BlockSoundProfile, wutils:WaveUtils) -> None:
        super().__init__(bsd, wutils)
        self._meta_data = None
        _ = self.meta_data

    @property
    def meta_data(self):
        if self._meta_data is None:
            raw_bits = self._get_raw_bit()
            meta_bits = self._get_block_bits(raw_bits)
            reserved = BitsUtils.bits_to_int(meta_bits[0:32])
            frequency = BitsUtils.bits_to_int(meta_bits[32:32+16])
            reader_version = BitsUtils.bits_to_int(meta_bits[32+16:32+16+16])
            bitp_version = BitsUtils.bits_to_int(meta_bits[32+16+16:32+16+16+16]) 
            wave_version = BitsUtils.bits_to_int(meta_bits[32+16+16+16:32+16+16+16+16])
            self._meta_data = MetaData(reserved, frequency, reader_version, bitp_version, wave_version)
        return self._meta_data