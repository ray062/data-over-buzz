# demodulation
# User Notes : Do remember to turn off all sound enhancement features on your device : Equalizer, Dolby effect etc.
# User Notes : Do turn the output devise to 80% volume
# User Notes : Set the receiver the frame rate to 192000. The heigher the better. mono or 2 channel, 2 bytes (16bits) sample width is good enough. 
# User Notes : If the frame rate cannot be set to 192000 or higher, the sound frequency must be set lower. It should not be more than 1/6 of frame rate. For example, for 44100 fram rate, the max frequency is 44100/6=7350

# Attention, the real frequency could be very near to the nominal one but still a little bit different. 
# With a long duration audio, the cumulated shift and float error could be large enough to break the demodulation. 
# The way used here to avoid this is split the data into chunks inside one audio. At each chunk, the 1st cycle position is recalculated

# Attention, with High freq (32khz), the 1st "1" bit cycle after some "0" bit cycles tends to be less loud than then expected.
# By consequence, the 1st "1" bit could be truncated as it's not consedered as the 1st cycle 
# To handle this, it's necessary to lower the max_volume threshold (reduced from 0.9 to 0.8) and put the signal "1" bits longer (changed from 20 to 100)
# Or, dynamically calculate the length of a header/chunk as the first "1"s' length is not fix. Here, the dynamic method is used

# Note : 32khz seems to be the limit. As some unreliabilities emerged beginning with this frequency and to handle these unreliabilities, the code is much more complexe than before to handle these issues.
# Note : At 32khz, the transfer rate would be : 32000/8 = 4000B/sec

import struct
import wave
import zlib
import logging
from dataclasses import dataclass

_logger = logging.getLogger(__name__)

def open_file_in_bits(file_path)->str:
    rlt = ""
    with open(file_path, 'rb') as f:
        while True:
            byte = f.read(1)
            if not byte:
                break
            rlt = f"{rlt}{bin(ord(byte))[2:].zfill(8)}"
    return rlt

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



class BitsUtils:
    @classmethod
    def purge_beginning_ones(cls, raw_bits:str):
        original_len = len(raw_bits)
        purged_bits = raw_bits.lstrip("1")
        purged_len = len(purged_bits)
        starting_ones_count = original_len - purged_len
        return purged_bits, starting_ones_count

    @classmethod
    def bits_to_int(cls, bits:str):
        return int(bits, 2)

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


class ByteUtils:
    @classmethod
    def bits_to_bytes(cls, bits:str)->bytes:
        fmt = 'B' * ((len(bits) + 7) // 8)
        packed = struct.pack(fmt, *[sum(b << 7-i for i, b in enumerate(map(int, bits[n:n+8]))) for n in range(0, len(bits), 8)])
        return packed
    
    @classmethod
    def checksum(cls, bytes_content:bytes)->int:
        return zlib.adler32(bytes_content)
    
    @classmethod
    def save_bytes_to_file(cls, bytes_content:bytes, file_path):
        with open(file_path, 'wb') as f:
            f.write(bytes_content)

class DemodWorkflow:
    VERSION=1

    def __init__(self) -> None:
        pass

    def execute(self, wave_file_path:str, output_file_path:str, start_at:int):
        reader = WaveReader(wave_file_path)
        wutils = WaveUtils(reader)
        
        meta_bsp = BlockSoundProfile(
            sound_data = reader.data, 
            freq = MetaDataDemod.META_FREQ, 
            frame_rate = reader.frame_rate, 
            block_bits_number = MetaDataDemod.BLOCK_BITS_NUMBER,
            search_sec = start_at, 
            beginning_ones_number = MetaDataDemod.BEGINNING_ONES_NUMBER,
            beginning_ones_threshold = MetaDataDemod.BEGINNING_ONES_THRESHOLD, 
            beginning_void_zero_number = MetaDataDemod.BEGINNING_VOID_ZERO_NUMBER
        )

        meta_mod = MetaDataDemod(meta_bsp, wutils)
        meta_data = meta_mod.meta_data
        remaining_sound_data = meta_mod.remaining_sound_data
        _logger.debug("Meta data: %s", meta_data)

        if not MetaData.compatible_check(meta_data):
            raise ValueError("The sound is not compatible.")
        
        header_bsp = BlockSoundProfile(
            sound_data = remaining_sound_data,
            freq = meta_data.frequency,
            frame_rate = reader.frame_rate,
            block_bits_number = HeaderDataDemod.BLOCK_BITS_NUMBER,
            search_sec = HeaderDataDemod.BEGINNING_ONES_NUMBER * 4 / meta_data.frequency,
            beginning_ones_number=HeaderDataDemod.BEGINNING_ONES_NUMBER,
            beginning_ones_threshold=HeaderDataDemod.BEGINNING_ONES_THRESHOLD,
            beginning_void_zero_number=HeaderDataDemod.BEGINNING_VOID_ZERO_NUMBER
        )

        header_mod = HeaderDataDemod(header_bsp, wutils)
        header_data = header_mod.header_data
        remaining_sound_data = header_mod.remaining_sound_data
        _logger.debug("Header data: %s", header_data)

        chunk_bsp = BlockSoundProfile(
            sound_data = remaining_sound_data,
            freq = meta_data.frequency,
            frame_rate = reader.frame_rate,
            block_bits_number = FileDataDemod.BEGINNING_ONES_NUMBER + FileDataDemod.BEGINNING_VOID_ZERO_NUMBER + header_data.chunk_size,
            search_sec = FileDataDemod.BEGINNING_ONES_NUMBER * 4 / meta_data.frequency,
            beginning_ones_number=FileDataDemod.BEGINNING_ONES_NUMBER,
            beginning_ones_threshold=FileDataDemod.BEGINNING_ONES_THRESHOLD,
            beginning_void_zero_number=FileDataDemod.BEGINNING_VOID_ZERO_NUMBER
        )
        file_bits = FileDataDemod(chunk_bsp, wutils, meta_data, header_data).demod_file_data()
        file_bytes = ByteUtils.bits_to_bytes(file_bits)
        checksum = ByteUtils.checksum(file_bytes)
        if checksum != header_data.checksum:
            raise ValueError("Checksum does not match.")
        ByteUtils.save_bytes_to_file(file_bytes, output_file_path)
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="input file path") 
    parser.add_argument("output_file", help="output file path")
    parser.add_argument("-s", "--start-at", type=int, default=2, help="start at sec")
    parser.add_argument("-l", "--log-level", default="INFO", help="logging level")

    args = parser.parse_args()
    input_file = args.input_file
    output_file = args.output_file
    start_at = args.start_at
    log_level = args.log_level

    logging_levels = {
        logging.getLevelName(logging.DEBUG): logging.DEBUG,
        logging.getLevelName(logging.INFO): logging.INFO, 
        logging.getLevelName(logging.WARNING): logging.WARNING,
        logging.getLevelName(logging.ERROR): logging.ERROR,
        logging.getLevelName(logging.CRITICAL): logging.CRITICAL
    }

    logging.basicConfig(level=logging_levels[log_level], format='[%(levelname)s] %(asctime)s - %(message)s')
    _logger.info(f"Input file: {input_file}")
    _logger.info(f"Output file: {output_file}")
    _logger.info(f"Start at: {start_at}")
    _logger.info(f"Log level: {log_level}")
    DemodWorkflow().execute(args.input_file, args.output_file, args.start_at)
    _logger.info("All Done!")
