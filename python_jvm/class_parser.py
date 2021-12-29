from dataclasses import dataclass, field#, KW_ONLY
from typing import List
import mmap
import logging
from textwrap import dedent
level = logging.ERROR
logging.basicConfig(
    encoding='utf-8', 
    level=level)
# from struct import unpack
filename = "./HelloWorld.class"

std_method = {
    'java/lang/System': {
        'out':{
            'println': lambda x: print(x[0])
        }
    }
}

class REPR:
    def __repr__(self):
        attr_exp = ",".join([f'{k} = {v}' for k, v in vars(self).items()])
        return f'''{str(type(self))}({attr_exp})'''

class CONSTANT(REPR):
    cp_index: bytes

class CONSTANT_Methodref(CONSTANT):
    class_index: int # 2 bytes
    name_and_type_index: int # 2bytes
    def __init__(self, f):
        self.class_index = parse_int(f.read(2))
        self.name_and_type_index = parse_int(f.read(2))
        
class CONSTANT_Class(CONSTANT):
    name_index: int # 2bytes
    def __init__(self, f):
        self.name_index = parse_int(f.read(2))

class CONSTANT_NameAndType(CONSTANT):
    name_index: int # 2bytes
    descriptor_index: int # 2 bytes
    def __init__(self, f):
        self.name_index = parse_int(f.read(2))
        self.descriptor_index = parse_int(f.read(2))

class CONSTANT_Utf8(CONSTANT):
    info: bytes
    def __init__(self, f):
        length = parse_int(f.read(2))
        self.info = f.read(length)

class CONSTANT_Fieldref(CONSTANT):
    class_index: int # 2 bytes
    name_and_type_index: int # 2 bytes
    def __init__(self, f):
        self.class_index = parse_int(f.read(2))
        self.name_and_type_index = parse_int(f.read(2))

class CONSTANT_String(CONSTANT):
    string_index: int # 2 bytes
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



@dataclass
class ClassFile:
    # _: KW_ONLY
    magic: bytes # 4 bytes
    minor_version: int # 2bytes
    major_version: int # 2bytes
    constant_pool_count: bytes #2bytes
    constant_pool: List[CONSTANT] = field(default_factory=list)
    access_flags: bytes = field(default_factory=bytes)# 2bytes
    this_class: bytes = field(default_factory=bytes)# 2bytes
    super_class: bytes = field(default_factory=bytes)# 2bytes
    interfaces_count: int = field(default_factory=int)# 2bytes
    # skip interfaces 
    fields_count: int = field(default_factory=int)# 2bytes
    # skip fields
    methods_count: int = field(default_factory=int)# 2bytes
    methods: List[Method] = field(default_factory=list)
    attributes_count: int = field(default_factory=int)# 2bytes
    attributes: List[Attribute] = field(default_factory=list)

def hexdump(b: bytes):
    return "".join([f"{i:02x} " for i in b])

def parse_int(b: bytes) -> int:
    return int.from_bytes(b, byteorder='big')

def constant_pool_type(b: bytes) -> type: 
    i = parse_int(b)
    if i == 1:
        return CONSTANT_Utf8
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

def run(code: bytes, c: ClassFile):
    with mmap.mmap(-1, len(code)) as mm:
        mm.write(code)
        mm.seek(0)
        max_stack = parse_int(mm.read(2))
        max_locals = parse_int(mm.read(2))
        code_length = parse_int(mm.read(4))
        logging.debug(f'max_stack {max_stack}')
        logging.debug(f'max_locals {max_locals}')
        logging.debug(f'code_length {code_length}')
        stack = []
        return_value = None
        local_variables = [None for _ in range(max_locals)]
        while True:
            opcode: bytes = mm.read(1)

            logging.debug(dedent(f'''
            ########################
            current position {mm.tell() - 1 - 8}
            opcode {hexdump(opcode)}
            stack {stack}
            local_variables {local_variables}
            ########################
            '''))
            if opcode == b'\x03':
                logging.info('OPCODE: iconst_0')
                stack.append(0)
            elif opcode == b'\x04':
                logging.info('OPCODE: iconst_1')
                stack.append(1)
            elif opcode == b'\x05':
                logging.info('OPCODE: iconst_2')
                stack.append(2)
            elif opcode == b'\x08':
                logging.info('OPCODE: iconst_5')
                stack.append(5)
            elif opcode == b'\x10':
                logging.info('OPCODE: bipush')
                val = parse_int(mm.read(1))
                stack.append(val)
            elif opcode == b'\x12':
                logging.info('OPCODE: ldc')
                pool_index = parse_int(mm.read(1))
                symbol_name_index = c.constant_pool[pool_index-1]
                string = c.constant_pool[symbol_name_index.string_index-1].info.decode()
                stack.append(string)
            elif opcode == b'\x15':
                logging.info('OPCODE: iload')
                index = parse_int(mm.read(1))
                stack.append(local_variables[index-1])
            elif opcode == b'\x1b':
                logging.info('OPCODE: iload_1')
                stack.append(local_variables[0])
            elif opcode == b'\x1c':
                logging.info('OPCODE: iload_2')
                stack.append(local_variables[1])
            elif opcode == b'\x1d':
                logging.info('OPCODE: iload_3')
                stack.append(local_variables[2])
            elif opcode == b'\x36':
                logging.info('OPCODE: istore')
                val = stack.pop()
                index = parse_int(mm.read(1))
                local_variables[index-1] = val
            elif opcode == b'\x3c':
                logging.info('OPCODE: istore_1')
                local_variables[0] = stack.pop()
            elif opcode == b'\x3d':
                logging.info('OPCODE: istore_2')
                local_variables[1] = stack.pop()
            elif opcode == b'\x3e':
                logging.info('OPCODE: istore_3')
                local_variables[2] = stack.pop()
            elif opcode == b'\x60':
                logging.info('OPCODE: iadd')
                val1 = stack.pop()
                val2 = stack.pop()
                logging.debug(f"iadd {val1} + {val2}")
                stack.append(val1 + val2)
            elif opcode == b'\x84':
                logging.info('OPCODE: iinc')
                target = parse_int(mm.read(1))
                val = parse_int(mm.read(1))
                local_variables[target - 1] += val
            elif opcode == b'\xa2':
                logging.info('OPCODE: if_icmpge')
                branch1 = parse_int(mm.read(1))
                branch2 = parse_int(mm.read(1))
                value2 = stack.pop()
                value1 = stack.pop()
                logging.debug(f'value1: {value1} value2: {value2}')
                if value1 >= value2:
                    offset = int.from_bytes((branch1 << 8 | branch2).to_bytes(2, byteorder='big'), signed=True, byteorder='big') - 3
                    logging.debug(f'seek to {offset}')
                    mm.seek(offset, 1)
                else:
                    # logging.debug(f'seek to {branch2}')
                    # mm.read(branch2)
                    pass
            elif opcode == b'\xa7':
                logging.info('OPCODE: goto')
                branch1 = parse_int(mm.read(1))
                branch2 = parse_int(mm.read(1))
                offset = int.from_bytes((branch1 << 8 | branch2).to_bytes(2, byteorder='big'), signed=True, byteorder='big') - 3
                logging.debug(f"goto offset {offset}")
                mm.seek(offset, 1)


            elif opcode == b'\xb2':
                logging.info('OPCODE: getstatic')
                pool_index = parse_int(mm.read(2))
                symbol_name: CONSTANT_Fieldref = c.constant_pool[pool_index-1]
                assert isinstance(symbol_name, CONSTANT_Fieldref)
                callee_class = c.constant_pool[c.constant_pool[symbol_name.class_index-1].name_index-1].info.decode()
                field = c.constant_pool[c.constant_pool[symbol_name.name_and_type_index-1].name_index-1].info.decode()
                method_return = c.constant_pool[c.constant_pool[symbol_name.name_and_type_index-1].descriptor_index-1].info.decode()
                logging.debug(f'callee info, {callee_class}, {field}, {method_return}')

                stack.append({
                    'callable': {
                        'class': callee_class,
                        'field': field,
                        'return': method_return
                    }
                })
            elif opcode == b'\xb6':
                logging.info('OPCODE: invokevirtual')
                pool_index = parse_int(mm.read(2))
                symbol_name_index = c.constant_pool[pool_index-1]

                callee = c.constant_pool[symbol_name_index.name_and_type_index-1]
                callee_method = c.constant_pool[callee.name_index-1].info.decode() #println
                args_exp = c.constant_pool[callee.descriptor_index-1].info.decode()

                logging.debug(f'args_exp: {args_exp}')
                args = []
                # for _ in range(len(args_exp.split(';'))-1):
                for _ in range(1):
                    args.append(stack.pop())
                method = stack.pop()
                logging.debug(f'method: {method} args: {args}')

                std_method[method['callable']['class']][method['callable']['field']][callee_method](args)
                return_value = 'aaa'
            elif opcode == b'\xb1':
                logging.info('OPCODE: return')
                return
            elif opcode == b'\xb8':
                logging.info('OPCODE: invokestatic')
                indexbyte1 = parse_int(mm.read(1))
                indexbyte2 = parse_int(mm.read(1))
                logging.debug(f'indexbyte1 {indexbyte1} indexbyte2 {indexbyte2}')
                callee_cp_index = int.from_bytes((indexbyte1 << 8 | indexbyte2).to_bytes(2, byteorder='big'), signed=True, byteorder='big')
                logging.debug(f'callee_cp_index {callee_cp_index}')
                callee_class = c.constant_pool[c.constant_pool[c.constant_pool[callee_cp_index-1].class_index-1].name_index-1].info.decode()
                callee_method = c.constant_pool[c.constant_pool[c.constant_pool[callee_cp_index-1].name_and_type_index-1].name_index-1].info.decode()
                logging.debug(f'invokestatic {callee_class}.{callee_method}')
                
                callee_method_obj = find_method(c, callee_method)
                callee_code = find_code(callee_method_obj, c)
                run(callee_code, c)
            else:
                raise Exception(f'unknown opcode {opcode}')

def find_method(c :ClassFile, name:str) -> Method:
    for m in c.methods:
        cp_name = c.constant_pool[m.name_index-1]
        assert isinstance(cp_name, CONSTANT_Utf8)
        if cp_name.info == name.encode():
            return m
    return None

def find_code(m :Method, c: ClassFile) -> bytes:
    for a in m.attribute_info:
        cp_name = c.constant_pool[a.attribute_name_index-1]
        assert isinstance(cp_name, CONSTANT_Utf8)
        if cp_name.info == b'Code':
            return a.info
    return None


with open(filename, 'rb') as f:
    # read header
    c = ClassFile(
        magic=f.read(4),
        minor_version=parse_int(f.read(2)),
        major_version=parse_int(f.read(2)),
        constant_pool_count=parse_int(f.read(2))
    )
    for cpi in range(c.constant_pool_count - 1):
        cpt = constant_pool_type(f.read(1))
        cp = cpt(f)
        cp.index = cpi + 1
        c.constant_pool.append(cp)
    
    c.access_flags = f.read(2)
    c.this_class = f.read(2)
    c.super_class = f.read(2)
    c.interfaces_count = parse_int(f.read(2))
    c.fields_count = parse_int(f.read(2))
    c.methods_count = parse_int(f.read(2))

    for _ in range(c.methods_count):
        c.methods.append(Method(f))

    c.attributes_count = parse_int(f.read(2))

    for _ in range(c.attributes_count):
        c.attributes.append(Attribute(f))


    main_method = find_method(c, 'main')
    main_code = find_code(main_method, c)
    hex_exp = "".join([f"{i:02x} " for i in main_code])
    logging.debug(f'main code {hex_exp}')
    run(main_code, c)