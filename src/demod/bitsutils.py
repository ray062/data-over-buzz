

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
    