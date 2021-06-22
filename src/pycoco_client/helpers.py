def bool2byte(b: bool):
    if b:
        return b'\x01'
    else:
        return b'\x00'