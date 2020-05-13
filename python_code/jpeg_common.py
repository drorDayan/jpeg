level = "debug"
number_of_components = 3
Y_COMP_ID = 1
CB_COMP_ID = 2
CR_COMP_ID = 3

Y_INDEX_IN_YCBCR = 0
CB_INDEX_IN_YCBCR = 1
CR_INDEX_IN_YCBCR = 2

# lookup table you ugly bugly
def zig_zag_index(k, n=8):
    # upper side of interval
    if k >= n * (n + 1) // 2:
        i, j = zig_zag_index(n * n - 1 - k, n)
        return n - 1 - i, n - 1 - j
    # lower side of interval
    i = int((np.sqrt(1 + 8 * k) - 1) / 2)
    j = k - i * (i + 1) // 2
    return (j, i - j) if i & 1 else (i - j, j)

def zig_zag_value(i, j, n):
    # upper side of interval
    if i + j >= n:
        return n * n - 1 - zig_zag_value(n - 1 - i, n - 1 - j, n)
    # lower side of interval
    k = (i + j) * (i + j + 1) // 2
    return k + i if (i + j) & 1 else k + j

def debug_print(*arg, newline=True):
    if level == "debug":
        if newline:
            print(*arg)
        if not newline:
            print(*arg, end=" ")


def info_print(*arg, newline=True):
    if level == "info" or level == "debug":
        if newline:
            print(*arg)
        if not newline:
            print(*arg, end=" ")
