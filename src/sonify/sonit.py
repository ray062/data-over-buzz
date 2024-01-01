import logging
from .bitp import BitProcessor
from .readfile import InputReader

_logger = logging.getLogger(__name__)

class SonifyWorkflow:
    VERSION = 1
    # Compatible to work with : 
    #     InputReader Version 1
    #     BitProcessor Version 1
    #     WaveProcessor Version 1, 2
    #     OutputWriter Version 1, 2

    def __init__(self, frequency:int, frame_rate:int, chunk_kb_size:int, channel_number:int) -> None:
        self._freq = frequency
        self._frame_rate = frame_rate
        self._chunk_kb_size = chunk_kb_size
        self._one_bit_cycle_number = 1
        self._num_channels = channel_number

    def execute(self, input_filepath:str, output_filepath:str):
        # put them at the beginning to check input values before starting the workflow
        if self._num_channels == 1:
            from .wavep import WaveProcessorV1
            from .output import OutputWriterV1
            wavp = WaveProcessorV1(self._freq, self._frame_rate, self._one_bit_cycle_number)
            writer = OutputWriterV1()
        elif self._num_channels == 2:
            from .wavep import WaveProcessorV2
            from .output import OutputWriterV2
            wavp = WaveProcessorV2(self._freq, self._frame_rate, self._one_bit_cycle_number)
            writer = OutputWriterV2()
        else:
            raise ValueError("Invalid channel number")
        bitp = BitProcessor(self._chunk_kb_size*8*1024)
        _logger.info("Reading file...")
        reader = InputReader(input_filepath)
        checksum = reader.checksum

        with reader.open() as f:
            _logger.info("Processing file...")
            meta_bits, header_bits, chunked_bits_iters = bitp.bitit(f, checksum, self._freq, InputReader.VERSION, wavp.VERSION)

        _logger.info("Converting to sound...")
        sound_data = wavp.convert(meta_bits, header_bits, chunked_bits_iters)

        _logger.info("Saving to file...")
        writer.save(wavp, sound_data, output_filepath)
        