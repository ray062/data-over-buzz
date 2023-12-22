from dataclasses import dataclass


@dataclass
class BlockSoundProfile:
    sound_data:list[int]
    freq:int
    frame_rate:int
    block_bits_number:int # total number of bits of a block including beginning ones
    search_sec:float # till how many sec to search the max volume of the sound block
    beginning_ones_number:int
    beginning_ones_threshold:int
    beginning_void_zero_number:int=1

    @property
    def cycle_length(self):
        return self.frame_rate/self.freq