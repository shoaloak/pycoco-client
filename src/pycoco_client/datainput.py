def read_char(recv: [[int],any]):
    ch = recv(2)
    if (int(ch[0] | ch[1])) < 0:
        raise Exception("Invalid char received.")
    return ch

def read_ushort(recv):
    return int.from_bytes(recv(2), 'big')

def read_UTF(recv):
    utflen = read_ushort(recv)
    utf_string = recv(utflen)

    if len(utf_string) != utflen:
        raise Exception("UTF length mismatch")

    return utf_string.decode('utf-8')

def read_long(recv):
    return int.from_bytes(recv(8), 'big')

def read_varint(recv):
    val = b'\xff'[0] & recv(1)[0]
    if (val & 0x80) == 0:
        return val
    return val & 0x7f | read_varint(recv) << 7

def read_bool_array(recv):
    bool_arr = []
    bool_arr_len = read_varint(recv)
    for i in range(bool_arr_len):
        if (i % 8) == 0:
            buffer = int.from_bytes(recv(1), 'big')
        bool_arr.append((buffer & 0x01) != 0)
        buffer = buffer >> 1

    return bool_arr
