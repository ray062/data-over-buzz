import wave
import struct
import math
import zlib
import logging

_logger = logging.getLogger(__name__)

class InputReader:
    # Responsible of IO, compression, encryption
    VERSION = 1
    def __init__(self, input_filepath:str) -> None:
        self._input_filepath = input_filepath
        self._file_stream = None
        self._checksum = None

    def do(self):
        bitp = BitProcessor()
        with open(self._input_filepath, 'rb') as f:
            bitp = BitProcessor(f, self._chunk_bit_size)
        wavp = WaveProcessor(self._freq, self._frame_rate)
        self._sound_data = wavp.convert(bitp.enhanced_bits)
        wavp.save_to(self._sound_data, self._output_file)

    def __enter__(self):
        return self

    def open(self):
        if self._file_stream is not None:
            raise Exception("File stream is already opened")
        self._file_stream = open(self._input_filepath, 'rb')
        return self
    
    def read(self, nb_bytes=0):
        if nb_bytes == 0:
            return self._file_stream.read()
        else:
            return self._file_stream.read(nb_bytes)
    
    @property
    def checksum(self):
        if self._checksum is None:
            _logger.debug("Calculating checksum...")
            self.close()
            with self.open() as f:
                self._checksum = zlib.adler32(f.read())
                _logger.debug(f"Checksum:{self._checksum}")
        return self._checksum

    def close(self):
        if self._file_stream is not None:
            self._file_stream.close()
            self._file_stream = None
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

class BitProcessor:
    # Responsible of Bits
    VERSION = 1
    def __init__(self, chunk_bit_size:int) -> None:
        self._chunk_bit_size = chunk_bit_size
        _logger.debug(f"Chunk bit size:{chunk_bit_size}")

    def bitit(self, file_obj, checksum:int, frequency:int, reader_version:int, wave_version:int):
        file_bits = self._get_file_bits(file_obj)
        file_bits_number = len(file_bits)
        _logger.debug(f"File bit number:{file_bits_number}")
        meta_bits = self._gen_meta_bits(frequency, reader_version, wave_version)
        header_bits = self._gen_header_bits(checksum, file_bits_number)
        chunked_bits = self._chunknize(file_bits)
        return meta_bits, f"{header_bits}{chunked_bits}"

    def _get_file_bits(self, file_obj)->str:
        _logger.debug("Start get_file_bits")
        rlt = ""
        while True:
            byte = file_obj.read(1)
            if not byte:
                break
            rlt = f"{rlt}{bin(ord(byte))[2:].zfill(8)}"
        _logger.debug("End get_file_bits")
        return rlt
    
    def _gen_meta_bits(self, freq:int, reader_version:int, wave_version:int)->str:
        starting_bits = "1"*20
        starting_void_bits = "0"*1
        reserved_bits = "0"*8*4 # reserved bits are places for future extensions for backward compatibilities
        freq_data_bits = bin(freq)[2:].zfill(8*2)
        reader_version_bits = bin(reader_version)[2:].zfill(8*2)
        bitp_version_bits = bin(self.VERSION)[2:].zfill(8*2)
        wave_version_bits = bin(wave_version)[2:].zfill(8*2)
        ending_void_bits = "0"*3
        bits = f"{starting_bits}{starting_void_bits}{reserved_bits}{freq_data_bits}{reader_version_bits}{bitp_version_bits}{wave_version_bits}{ending_void_bits}"
        bit_length = len(bits)
        assert bit_length == 20+1+8*4+8*2+8*2+8*2+8*2+3, f"Unexpected meta bits length: {bit_length}" # expect 120
        return bits

    def _gen_header_bits(self, checksum:int, file_bits_number:int):
        # Responsible of sound wave 
        _logger.debug("Generating header bits...")
        starter = '1'*100
        starter_silent = '0'*7
        version_sig_str = "0"*31+"1" # Version 1
        checksum_sig_str = bin(checksum)[2:].zfill(32)
        assert len(checksum_sig_str) == 32, f"Bad checksum value: {checksum_sig_str} from {bin(checksum)[2:]} of {checksum}"
        chunk_number = math.ceil(file_bits_number / self._chunk_bit_size)
        chunk_number_sig_str = bin(chunk_number)[2:].zfill(32)
        chunk_size_sig_str = bin(self._chunk_bit_size)[2:].zfill(32)
        file_length_sig_str = bin(file_bits_number)[2:].zfill(64)
        reserved_sig_str = "0"*64
        post_sig_silent = '0'*7
        file_start_sig = '1'*7
        header_bits = f"{starter}{starter_silent}{version_sig_str}{checksum_sig_str}{chunk_number_sig_str}{chunk_size_sig_str}{file_length_sig_str}{reserved_sig_str}{post_sig_silent}{file_start_sig}"
        assert len(header_bits) == 100+7+32+32+32+32+64+64+7+7, f"Unexpected header bits length: {len(header_bits)}"
        return header_bits
    
    def _chunknize(self, bits:str)->str:
        _logger.debug("Generating chunked bits...")
        file_bits_number = len(bits)
        rlt = ""
        void = "0"*3
        start = "1"*3
        full_chunk_void = "0"*self._chunk_bit_size
        chunk_number = math.ceil(file_bits_number/self._chunk_bit_size)
        _logger.debug(f"Chunk number:{chunk_number}")
        for i in range(chunk_number):
            chunk_data = bits[i*self._chunk_bit_size:(i+1)*self._chunk_bit_size]
            if i == chunk_number - 1:
                chunk_data = f"{chunk_data}{full_chunk_void}"[:self._chunk_bit_size] # complete the last chunk with zeros
            chunk_data = f"{void}{start}0{chunk_data}{void}"
            rlt = f"{rlt}{chunk_data}"
        return rlt

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

class OutputWriter:
    VERSION = 1
    def __init__(self) -> None:
        self._num_channels = 1

    def save(self, wavp:WaveProcessor, sound_data:list[int], file_path:str):
        _logger.debug(f"Saving sound data to : {file_path}")
        frames = b''.join([struct.pack('h', int(s)) for s in sound_data])
        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setparams((wavp.channel_number, wavp.sample_width, wavp.frame_rate, len(sound_data), 'NONE', 'not compressed'))
            wav_file.writeframes(frames)

class SonifyWorkflow:
    VERSION = 1
    # Compatible to work with : 
    #     InputReader Version 1
    #     BitProcessor Version 1
    #     WaveProcessor Version 1
    #     OutputWriter Version 1

    def __init__(self, frequency:int, frame_rate:int, chunk_kb_size:int) -> None:
        self._freq = frequency
        self._frame_rate = frame_rate
        self._chunk_kb_size = chunk_kb_size
        self._one_bit_cycle_number = 1

    def execute(self, input_filepath:str, output_filepath:str):
        # put them at the beginning to check input values before starting the workflow
        wavp = WaveProcessor(self._freq, self._frame_rate, self._one_bit_cycle_number) 
        bitp = BitProcessor(self._chunk_kb_size*8*1024)
        writer = OutputWriter()

        _logger.info("Reading file...")
        reader = InputReader(input_filepath)
        checksum = reader.checksum

        with reader.open() as f:
            _logger.info("Processing file...")
            meta_bits, enhanced_bits = bitp.bitit(f, checksum, self._freq, InputReader.VERSION, WaveProcessor.VERSION)

        _logger.info("Converting to sound...")
        sound_data = wavp.convert(meta_bits, enhanced_bits)

        _logger.info("Saving to file...")
        writer.save(wavp, sound_data, output_filepath)
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="input file path") 
    parser.add_argument("output_file", help="output file path")
    parser.add_argument("-f", "--frequency", type=int, default=32000, help="frequency")
    parser.add_argument("-r", "--frame-rate", type=int, default=192000, help="frame rate")  
    parser.add_argument("-c", "--chunk-size", type=int, default=1, help="chunk size in KB")
    parser.add_argument("-l", "--log-level", default="INFO", help="logging level")

    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file 
    frequency = args.frequency
    frame_rate = args.frame_rate
    chunk_size = args.chunk_size
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
    _logger.info(f"Frequency: {frequency}")
    _logger.info(f"Frame rate: {frame_rate}")
    _logger.info(f"Chunk size: {chunk_size}")
    _logger.info(f"Version: {SonifyWorkflow.VERSION}")
    _logger.info(f"Log level: {log_level}")

    wf = SonifyWorkflow(frequency, frame_rate, chunk_size)
    wf.execute(input_file, output_file)
    _logger.info("All Done!")
