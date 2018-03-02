"""
@package simulator
encoder module
"""


def encoder(line):
    encoded_line = ""
    current = line[0]
    count = 0
    for index in line:
        if index == current:
            count += 1
            current = index
            pass
        if index != current and count == 1:
            encoded_line += current
            current = index
            pass
        if index != current and count > 1:
            encoded_line += str(count) + "" + current
            count = 1
            current = index
            pass
    if count > 1:
        encoded_line += str(count) + "" + current
    else:
        encoded_line += current
    count = None
    current = None

    return encoded_line
