level = "debug"
number_of_components = 3
Y_COMP_ID = 1
CB_COMP_ID = 2
CR_COMP_ID = 3

Y_INDEX_IN_YCBCR = 0
CB_INDEX_IN_YCBCR = 1
CR_INDEX_IN_YCBCR = 2
import time

def time_me(f, x):
    b = time.time()
    y = f(x)
    e = time.time()
    print(e-b)
    return y


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
