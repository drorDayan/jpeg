level = "debug"
number_of_components = 3


def debug_print(*arg, newline=True):
    if level == "debug" or level == "info":
        if newline:
            print(*arg)
        if not newline:
            print(*arg, end=" ")


def info_print(*arg, newline=True):
    if level == "info":
        if newline:
            print(*arg)
        if not newline:
            print(*arg, end=" ")
