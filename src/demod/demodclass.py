import logging
from .waveutils import WaveUtils
from .soundprofile import BlockSoundProfile
from .bitsutils import BitsUtils

_logger = logging.getLogger(__name__)

class BlockDataDemod:
    def __init__(self, bsp:BlockSoundProfile, wutils:WaveUtils) -> None:
        self._bsp = bsp
        self._wutils =  wutils
        self._first_cycle_index = None
        self._block_data = None
        self._remaining_sound_data_index = None

    def _get_raw_bit(self):
        block_sound, self._first_cycle_index = self._wutils.find_sound_data_block(self._bsp.sound_data,
                                                                                  self._bsp.freq,
                                                                                  self._bsp.block_bits_number,
                                                                                  search_time_in_sec=self._bsp.search_sec)
        max_volume = self._wutils.find_max_volume(block_sound, search_time_in_sec=self._bsp.beginning_ones_number*2/self._bsp.freq)
        return self._wutils.demod_to_bits(block_sound, self._bsp.freq, 0, max_volume)
    
    def _get_block_bits(self, raw_bits:str):
        if raw_bits[:self._bsp.beginning_ones_number].find("1"*self._bsp.beginning_ones_threshold)<0: # Find in the first ${block_bits_number} bits if there are ${beginning_ones_threshold} continue "1"s then it's considered as the header.
            _logger.debug(f"Beginning bits: {raw_bits[:self._bsp.beginning_ones_number]}")
            raise ValueError("Cannot find the block data")
        purged_bits, starting_ones_count = BitsUtils.purge_beginning_ones(raw_bits)
        self._remaining_sound_data_index = int(self._first_cycle_index + (self._bsp.cycle_length * (self._bsp.block_bits_number - self._bsp.beginning_ones_number + starting_ones_count)))
        _logger.debug(f"Starting ones: {starting_ones_count}, First cycle index: {self._first_cycle_index}, Remining index: {self._remaining_sound_data_index}")
        return purged_bits[self._bsp.beginning_void_zero_number:self._bsp.beginning_void_zero_number + self._bsp.block_bits_number - self._bsp.beginning_ones_number - self._bsp.beginning_void_zero_number]
    
    @property
    def remaining_sound_data(self):
        if self._remaining_sound_data_index is None:
            raise ValueError("Cannot get the remaining sound data")
        return self._bsp.sound_data[self._remaining_sound_data_index:]
    
    