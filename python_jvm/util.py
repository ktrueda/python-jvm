def hexdump(b: bytes):
    return "".join([f"{i:02x} " for i in b])

def parse_int(b: bytes) -> int:
    return int.from_bytes(b, byteorder='big')