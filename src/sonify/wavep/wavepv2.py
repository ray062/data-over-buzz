import math
import logging
from .iwavep import WaveProcessor

_logger = logging.getLogger(__name__)

class WaveProcessorV2(WaveProcessor):
    VERSION = 2
    def __init__(self, frequency:int, frame_rate:int, one_bit_cycle_number:int = 1) -> None:
        super().__init__(frequency, frame_rate, one_bit_cycle_number)
        self._num_channels = 2
        self._right_channel_starting_bits = "1"*20+"0"
    
    def _calculate_one_channel_chunk_number(self, meta_sound_length:int, header_sound_length:int, one_chunk_bits_number:int, chunk_number:int):
        assert self.channel_number == 2, "WaveProcessorV2 only support 2 channels"
        one_chunk_sound_len = self._one_bit_cycle_frame * one_chunk_bits_number

        left_overhead_chunk_number = math.ceil((meta_sound_length + header_sound_length) / one_chunk_sound_len)
        _logger.debug(f"left_overhead_chunk_number: {left_overhead_chunk_number}")
        right_overhead_chunk_number = 1 # a fixed value, one chunk it makes the right one channel longer

        raw_one_channel_chunk_number = math.ceil(chunk_number / self.channel_number)
        raw_left_channel_chunk_number = raw_one_channel_chunk_number
        _logger.debug(f"raw_left_channel_chunk_number: {raw_left_channel_chunk_number}")
        raw_right_channel_chunk_number = chunk_number - raw_left_channel_chunk_number # could be 1 less than the left one
        _logger.debug(f"raw_right_channel_chunk_number: {raw_right_channel_chunk_number}")

        left_extra_overhead_number = left_overhead_chunk_number - right_overhead_chunk_number
        _logger.debug(f"left_extra_overhead_number: {left_extra_overhead_number}")
        balanced_extra_overhead_number = 0
        if left_extra_overhead_number >0:
            balanced_extra_overhead_number = math.ceil((left_extra_overhead_number - (raw_left_channel_chunk_number - raw_right_channel_chunk_number))/self.channel_number)
        _logger.debug(f"balanced_extra_overhead_number: {balanced_extra_overhead_number}")
        left_channel_chunk_number = raw_left_channel_chunk_number + left_overhead_chunk_number - balanced_extra_overhead_number
        right_channel_chunk_number = raw_right_channel_chunk_number + right_overhead_chunk_number + balanced_extra_overhead_number
        assert left_channel_chunk_number == right_channel_chunk_number, f"Left and right channel chunk number should be equal. Got {left_channel_chunk_number} vs {right_channel_chunk_number}"
        return left_channel_chunk_number, raw_left_channel_chunk_number, balanced_extra_overhead_number


    def _get_sound(self, bits:str):
        sample_number = self._get_sample_number(self._freq, self._one_bit_cycle_number, len(bits))
        full_init_sound = self._gen_full_init_sound(self._freq, sample_number)
        sound_data = self._mask_sound_by_bits(full_init_sound, self._one_bit_cycle_frame, bits)
        return sound_data
    
    def _get_left_channel_sound(self, meta_sound:list[int], bits:str, expected_sound_length:int):
        sound_data = meta_sound + self._get_sound(bits)
        sound_data = sound_data + [0] * int(expected_sound_length - len(sound_data))
        return sound_data
    
    def _get_right_channel_sound(self, bits:str, expected_sound_length:int):
        sound_data = self._get_sound(bits)
        sound_data = sound_data + [0] * int(expected_sound_length - len(sound_data))
        return sound_data

    def convert(self, meta_bits:str, header_bits:str, chunked_bits_iter)->list[tuple[int,int]]:
        _logger.debug("Converting...")
        meta_sound= self._get_meta_sound(meta_bits)
        meta_sound_len = len(meta_sound)
        _logger.debug(f"Meta sound len:{meta_sound_len}")
        header_sound_len = len(header_bits) * self._one_bit_cycle_frame
        _logger.debug(f"Header sound len:{header_sound_len}")
        chunked_bits_list = list(chunked_bits_iter)
        chunk_number = len(chunked_bits_list)
        _logger.debug(f"Chunk number:{chunk_number}")
        one_chunk_sound_len = self._one_bit_cycle_frame * len(chunked_bits_list[0])
        _logger.debug(f"One chunk sound len:{one_chunk_sound_len}")

        one_channel_chunk_number, raw_left_channel_chunk_number, balanced_extra_overhead_number  = self._calculate_one_channel_chunk_number(meta_sound_len, header_sound_len, one_chunk_sound_len, chunk_number)

        chunked_bits_cut_index = raw_left_channel_chunk_number - balanced_extra_overhead_number
        left_channel_bits = header_bits + "".join(chunked_bits_list[:chunked_bits_cut_index])
        right_channel_bits = self._right_channel_starting_bits+"".join(chunked_bits_list[chunked_bits_cut_index:])
        expected_sound_length = one_channel_chunk_number * one_chunk_sound_len

        left_channel_sound_data = self._get_left_channel_sound(meta_sound, left_channel_bits, expected_sound_length)
        right_channel_sound_data = self._get_right_channel_sound(right_channel_bits, expected_sound_length)

        assert len(left_channel_sound_data) == len(right_channel_sound_data), f"Left & Right channels sound length should be equal. len({left_channel_sound_data}) vs {len(right_channel_sound_data)}"
        zipped = list(zip(left_channel_sound_data, right_channel_sound_data))
        return zipped

    @property
    def channel_number(self):
        return self._num_channels
    
    @property
    def sample_width(self):
        return self._sample_width
    
    @property
    def frame_rate(self):
        return self._frame_rate
    