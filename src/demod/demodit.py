import logging
from .waveutils import WaveUtils
from .bytesutils import BytesUtils
from .soundprofile import BlockSoundProfile
from .readwave import WaveReader
from .demodmeta import MetaDataDemod, MetaData
from .demodheader import HeaderDataDemod
from .demodfile import FileDataDemod

_logger = logging.getLogger(__name__)

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
        file_bytes = BytesUtils.bits_to_bytes(file_bits)
        checksum = BytesUtils.checksum(file_bytes)
        if checksum != header_data.checksum:
            raise ValueError("Checksum does not match.")
        BytesUtils.save_bytes_to_file(file_bytes, output_file_path)
        