from dataclasses import dataclass, field  # , KW_ONLY
from typing import Dict, List, Type, TypeVar
from python_jvm.util import parse_int


class REPR:
    def __repr__(self):
        attr_exp = ",".join([f'{k} = {v}' for k, v in vars(self).items()])
        return f'''{str(type(self))}({attr_exp})'''


class CONSTANT(REPR):
    pass


class CONSTANT_Methodref(CONSTANT):
    class_index: int  # 2 bytes
    name_and_type_index: int  # 2bytes

    def __init__(self, f):
        self.class_index = parse_int(f.read(2))
        self.name_and_type_index = parse_int(f.read(2))


class CONSTANT_Class(CONSTANT):
    name_index: int  # 2bytes

    def __init__(self, f):
        self.name_index = parse_int(f.read(2))


class CONSTANT_NameAndType(CONSTANT):
    name_index: int  # 2bytes
    descriptor_index: int  # 2 bytes

    def __init__(self, f):
        self.name_index = parse_int(f.read(2))
        self.descriptor_index = parse_int(f.read(2))


class CONSTANT_Utf8(CONSTANT):
    info: bytes

    def __init__(self, f):
        length = parse_int(f.read(2))
        self.info = f.read(length)


class CONSTANT_Integer(CONSTANT):
    value: int

    def __init__(self, f):
        self.value = parse_int(f.read(4))


class CONSTANT_Fieldref(CONSTANT):
    class_index: int  # 2 bytes
    name_and_type_index: int  # 2 bytes

    def __init__(self, f):
        self.class_index = parse_int(f.read(2))
        self.name_and_type_index = parse_int(f.read(2))


class CONSTANT_String(CONSTANT):
    string_index: int  # 2 bytes

    def __init__(self, f):
        self.string_index = parse_int(f.read(2))


class Attribute(REPR):
    attribute_name_index: int
    attribute_length: int
    info: bytes

    def __init__(self, f):
        self.attribute_name_index = parse_int(f.read(2))
        self.attribute_length = parse_int(f.read(4))
        self.info = f.read(self.attribute_length)


class Method(REPR):
    access_flags: bytes
    name_index: int
    descriptor_index: int
    attribute_count: int
    attribute_info: List[Attribute]

    def __init__(self, f):
        self.access_flags = f.read(2)
        self.name_index = parse_int(f.read(2))
        self.descriptor_index = parse_int(f.read(2))
        self.attribute_count = parse_int(f.read(2))
        self.attribute_info = []
        for _ in range(self.attribute_count):
            self.attribute_info.append(Attribute(f))


class Code(REPR):
    max_stack: int
    max_locals: int
    code_length: int
    code: bytes

    def __init__(self, f):
        self.max_stack = parse_int(f[0:2])
        self.max_locals = parse_int(f[2:4])
        self.code_length = parse_int(f[4:8])
        self.code = f[8:]


tCONSTANT = TypeVar('tCONSTANT',
                    CONSTANT_Class,
                    CONSTANT_Fieldref,
                    CONSTANT_Integer,
                    CONSTANT_Methodref,
                    CONSTANT_NameAndType,
                    CONSTANT_String
                    )


@dataclass
class ClassFile:
    magic: bytes  # 4 bytes
    minor_version: int  # 2bytes
    major_version: int  # 2bytes
    constant_pool: Dict[int, tCONSTANT] = field(default_factory=dict)
    access_flags: bytes = field(default_factory=bytes)  # 2bytes
    this_class: int = field(default_factory=int)  # 2bytes
    super_class: bytes = field(default_factory=bytes)  # 2bytes
    interfaces_count: int = field(default_factory=int)  # 2bytes
    # skip interfaces
    fields_count: int = field(default_factory=int)  # 2bytes
    # skip fields
    methods_count: int = field(default_factory=int)  # 2bytes
    methods: List[Method] = field(default_factory=list)
    attributes_count: int = field(default_factory=int)  # 2bytes
    attributes: List[Attribute] = field(default_factory=list)


def constant_pool_type(b: bytes) -> type:
    i = parse_int(b)
    if i == 1:
        return CONSTANT_Utf8
    elif i == 3:
        return CONSTANT_Integer
    elif i == 7:
        return CONSTANT_Class
    elif i == 8:
        return CONSTANT_String
    elif i == 9:
        return CONSTANT_Fieldref
    elif i == 10:
        return CONSTANT_Methodref
    elif i == 12:
        return CONSTANT_NameAndType
    else:
        raise Exception(f'unknown constant pool type {i}')


def read_classfile(filepath: str) -> ClassFile:

    with open(filepath, 'rb') as f:
        # read header
        c = ClassFile(
            magic=f.read(4),
            minor_version=parse_int(f.read(2)),
            major_version=parse_int(f.read(2)),
        )
        constant_pool_count = parse_int(f.read(2)) - 1
        for cpi in range(constant_pool_count):
            cpt = constant_pool_type(f.read(1))
            cp = cpt(f)
            c.constant_pool[cpi + 1] = cp

        c.access_flags = f.read(2)
        c.this_class = parse_int(f.read(2))
        c.super_class = f.read(2)
        c.interfaces_count = parse_int(f.read(2))
        c.fields_count = parse_int(f.read(2))
        c.methods_count = parse_int(f.read(2))

        for _ in range(c.methods_count):
            c.methods.append(Method(f))

        c.attributes_count = parse_int(f.read(2))

        for _ in range(c.attributes_count):
            c.attributes.append(Attribute(f))
    return c
