import math
import logging
from .iwavep import WaveProcessor

_logger = logging.getLogger(__name__)

class WaveProcessorV1(WaveProcessor):
    VERSION = 1
    def __init__(self, frequency:int, frame_rate:int, one_bit_cycle_number:int = 1) -> None:
        super().__init__(frequency, frame_rate, one_bit_cycle_number)
        self._num_channels = 1
    
    def convert(self, meta_bits:str, header_bits:str, chucked_bits_iter)->list[int]:
        _logger.debug("Converting...")
        enhanced_bits = f"{header_bits}{''.join(chucked_bits_iter)}"
        sample_number = self._get_sample_number(self._freq, self._one_bit_cycle_number, len(enhanced_bits))
        _logger.debug(f"Sample number:{sample_number}")
        full_init_sound = self._gen_full_init_sound(self._freq, sample_number)
        sound_data = self._get_meta_sound(meta_bits) + self._mask_sound_by_bits(full_init_sound, self._one_bit_cycle_frame, enhanced_bits)
        return sound_data

    @property
    def channel_number(self):
        return self._num_channels
    
    @property
    def sample_width(self):
        return self._sample_width
    
    @property
    def frame_rate(self):
        return self._frame_rate
    