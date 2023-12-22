import logging
import math

_logger = logging.getLogger(__name__)

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
