
import struct
import zlib

class BytesUtils:
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