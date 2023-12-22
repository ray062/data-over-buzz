import logging
from .bitp import BitProcessor
from .wavep import WaveProcessor
from .output import OutputWriter
from .readfile import InputReader

_logger = logging.getLogger(__name__)

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