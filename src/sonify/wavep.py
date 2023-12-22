import math
import logging

_logger = logging.getLogger(__name__)

class WaveProcessor:
    VERSION = 1
    META_DATA_FREQ=1000
    def __init__(self, frequency:int, frame_rate:int, one_bit_cycle_number:int = 1) -> None:
        self._freq = frequency
        self._frame_rate = frame_rate
        assert frequency>=1000, f"The frequency is set too low ({frequency}), the minimum is 1000."
        assert frequency<=65536, f"The frequency is set too high ({frequency}), the maximum is 65536."
        assert frame_rate >= 44100, f"The frame rate is set too low ({frame_rate}). The minimum is 44100)"
        assert frame_rate <= 320000, f"The frame rate is set too high ({frame_rate}. The maximum is 320000)"
        assert frequency/frame_rate <= 1/6, f"The frequency is set too high ({frequency} regarding to the frame rate ({frame_rate}))"
        self._one_bit_cycle_number = one_bit_cycle_number
        assert one_bit_cycle_number>=1.0 and one_bit_cycle_number<=10.0, "Unexpect cycle number per bit. Got {one_bit_cycle_number}. Expect between 1 and 10."
        self._sample_width = 2
        self._max_volume = self.get_max_volume(self._sample_width)
        self._num_channels = 1
        self._one_bit_cycle_frame:float = self._one_bit_cycle_number / float(frequency) * float(frame_rate)
        assert self._one_bit_cycle_frame >= 6.0, f"Too few frames for one cycle. Got {self._one_bit_cycle_frame}, the minimum is 6." 

    def get_max_volume(self, sample_width=2):
        return float(2**(8*sample_width-1)-1)

    def _get_sample_number(self, freq:int, one_bit_cycle_number:int, bits_number:int)->int:
        one_bit_duration = one_bit_cycle_number/freq 
        return math.ceil(bits_number * one_bit_duration * self._frame_rate)

    def _gen_full_init_sound(self, freq:int, sample_number:int):
        _freq = float(freq)
        _frame_rate = float(self._frame_rate)
        return [self._max_volume * math.sin(2 * math.pi * _freq * (x / _frame_rate)) for x in range(sample_number)]
    
    def _get_meta_sound(self, meta_bits:str)->list[int]:
        sample_number = self._get_sample_number(self.META_DATA_FREQ, 1, len(meta_bits))
        init_sound = self._gen_full_init_sound(self.META_DATA_FREQ, sample_number)
        one_bit_cycle_frame = 1 / self.META_DATA_FREQ * self._frame_rate
        meta_sound = self._mask_sound_by_bits(init_sound, one_bit_cycle_frame, meta_bits)
        return meta_sound
    
    def _mask_sound_by_bits(self, init_sound:list[int], one_bit_cycle_frame:int, bits:str)->list[int]:
        sound_data = init_sound.copy()
        current_real_position = 0.0
        next_starting_position = 0
        for b in bits:
            next_real_position = current_real_position + one_bit_cycle_frame
            next_entire_position = int(next_real_position)
            if b=="0":
                for i in range(next_starting_position, next_entire_position):
                    sound_data[i] = 0
            current_real_position = next_real_position
            next_starting_position = next_entire_position
        return sound_data
    
    def convert(self, meta_bits:str, enhanced_bits:str)->list[int]:
        _logger.debug("Converting...")
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
    