'''
This is table 5
'''
# <dc_code> is decoding result gotten by using the huffman tree. <additional_bits> is the <dc_code> that follow right
# after <dc_code> is 8 bits (0..7), <additional_bit> is at most 16 bits (0..15)
def dc_value_encoding(dc_code : int, additional_bits : int):
    if dc_code == 0:
        return 0
    dc_value_sign = 1 if ((additional_bits & (1 << (dc_code -1))) > 0) else -1
    additional_bits_to_add = additional_bits & ((1 << (dc_code - 1)) - 1)

    if dc_value_sign:
        dc_value_base = 2 ** (dc_code - 1)
    else:
        dc_value_base = -1 * (2 ** dc_code - 1)

    return dc_value_sign * (dc_value_base + additional_bits_to_add)
