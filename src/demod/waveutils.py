import logging
from .readwave import WaveReader

_logger = logging.getLogger(__name__)

class WaveUtils:
    def __init__(self, wreader:WaveReader) -> None:
        self._wreader = wreader

    def find_max_volume(self, sound_data, search_time_in_sec=5):
        return max(sound_data[:int(self._wreader.frame_rate * search_time_in_sec)])

    def find_1st_cycle_index(self, sound_data, freq, search_time_in_sec=5):
        max_volume = self.find_max_volume(sound_data, search_time_in_sec=search_time_in_sec)
        end_position = int(self._wreader.frame_rate * search_time_in_sec)
        for i, d in enumerate(sound_data[:end_position]):
            if d>=max_volume*0.90:
                first_peak = i
                return max((int(first_peak - ((0.25/freq) * self._wreader.frame_rate))+1, 0))
        raise ValueError("Cannot find the 1st step index")
    
    def find_sound_data_block(self, sound_data, freq, nominal_bit_length, search_time_in_sec=5):
        first_cycle_index = self.find_1st_cycle_index(sound_data, freq, search_time_in_sec=search_time_in_sec)
        cycle_length = self._wreader.frame_rate/freq
        max_header_length = cycle_length * nominal_bit_length
        return sound_data[first_cycle_index:int(first_cycle_index+max_header_length) + 100], first_cycle_index # +100 for fault torelance
    
    def _demod_cycle(self, cycle_data, max_volume, cycle_length):
        _maxv = max(cycle_data)
        _minv = min(cycle_data)
        if _maxv >= 0.7 * max_volume or _minv <= -0.7*max_volume :
            return "1"
        
        if cycle_length == 2:
            borned_data = cycle_data
        elif cycle_length > 2 and cycle_length <= 10:
            borned_data = cycle_data[1:-1]
        elif cycle_length > 10:
            borned_width = int(cycle_length * 0.1)
            borned_data = cycle_data[borned_width:-borned_width]

        _maxv = max(borned_data)
        _minv = min(borned_data)
        if _maxv < 0.3 * max_volume and _minv > -0.3 * max_volume :
            return "0"
        _logger.debug(f"Cycle data lengthe : {len(cycle_data)}, Max: {_maxv}, Min:{_minv}, Max volume: {max_volume}")
        raise ValueError(f"Unexpected cycle data: {cycle_data}")
    
    def demod_to_bits(self, sound_data:list[int], freq:int, first_cycle_index:int, max_volume:int)->str:
        assert first_cycle_index>=0, f"Unexpect first_cycle_index value {first_cycle_index}"
        cycle_length = self._wreader.frame_rate/freq
        current_index = first_cycle_index
        current_real_position = first_cycle_index
        sound_data_length = len(sound_data)
        bits=""
        for i in range(int((sound_data_length-first_cycle_index)//cycle_length)-1):
            next_cycle_real_position = current_real_position + cycle_length
            current_index = int(current_real_position)
            next_cycle_index = int(next_cycle_real_position)
            try:
                cycle_data = sound_data[current_index:next_cycle_index]
                bits=f"{bits}{self._demod_cycle(cycle_data, max_volume, cycle_length)}"
            except Exception as e:
                print(f"Error occured at {current_index}:{next_cycle_index}")
                raise e
            else:
                current_real_position = next_cycle_real_position
                if current_real_position>=sound_data_length:
                    print("Meet the end of sound")
                    break
        return bits