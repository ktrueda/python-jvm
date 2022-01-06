import re
from typing import List


def hexdump(b: bytes):
    return "".join([f"{i:02x} " for i in b])


def parse_int(b: bytes) -> int:
    return int.from_bytes(b, byteorder='big')


def parse_arg_num(descriptor: str) -> int:
    start_index: int = descriptor.index('(') + 1
    end_index: int = descriptor.rindex(')')
    arg_exp: str = descriptor[start_index: end_index]
    arg_exp_class_replaced: List = []
    l_index = None
    for i, c in enumerate(arg_exp):
        if c == 'L':
            l_index = i
        elif c == ';':
            arg_exp_class_replaced.append('@')
            l_index = None
        elif not l_index:
            arg_exp_class_replaced.append(c)
    arg_exp_array_replaced: str = re.sub(r'\[.', '&', ''.join(arg_exp_class_replaced))
    return len(arg_exp_array_replaced)
