log_level = "info"

Y_COMP_ID = 1
CB_COMP_ID = 2
CR_COMP_ID = 3

Y_INDEX_IN_YCBCR = 0
CB_INDEX_IN_YCBCR = 1
CR_INDEX_IN_YCBCR = 2

ZIG_ZAG_LOOKUP = {0: (0, 0), 1: (0, 1), 2: (1, 0), 3: (2, 0), 4: (1, 1), 5: (0, 2), 6: (0, 3), 7: (1, 2), 8: (2, 1),
                  9: (3, 0), 10: (4, 0), 11: (3, 1), 12: (2, 2), 13: (1, 3), 14: (0, 4), 15: (0, 5), 16: (1, 4),
                  17: (2, 3), 18: (3, 2), 19: (4, 1), 20: (5, 0), 21: (6, 0), 22: (5, 1), 23: (4, 2), 24: (3, 3),
                  25: (2, 4), 26: (1, 5), 27: (0, 6), 28: (0, 7), 29: (1, 6), 30: (2, 5), 31: (3, 4), 32: (4, 3),
                  33: (5, 2), 34: (6, 1), 35: (7, 0), 36: (7, 1), 37: (6, 2), 38: (5, 3), 39: (4, 4), 40: (3, 5),
                  41: (2, 6), 42: (1, 7), 43: (2, 7), 44: (3, 6), 45: (4, 5), 46: (5, 4), 47: (6, 3), 48: (7, 2),
                  49: (7, 3), 50: (6, 4), 51: (5, 5), 52: (4, 6), 53: (3, 7), 54: (4, 7), 55: (5, 6), 56: (6, 5),
                  57: (7, 4), 58: (7, 5), 59: (6, 6), 60: (5, 7), 61: (6, 7), 62: (7, 6), 63: (7, 7)}


def zig_zag_index(k):
    # upper side of interval
    return ZIG_ZAG_LOOKUP[k]


def debug_print(*arg, newline=True):
    if log_level == "debug":
        if newline:
            print(*arg)
        if not newline:
            print(*arg, end=" ")


def info_print(*arg, newline=True):
    if log_level == "info" or log_level == "debug":
        if newline:
            print(*arg)
        if not newline:
            print(*arg, end=" ")
