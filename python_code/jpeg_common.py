use_debug_print = True


def debug_print(*arg, newline=True):
    if use_debug_print:
        if newline:
            print(*arg)
        if not newline:
            print(*arg, end=" ")
