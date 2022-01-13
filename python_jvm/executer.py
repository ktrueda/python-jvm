import mmap
import copy
from textwrap import dedent
from typing import Any, Dict, List, Optional, Union
from python_jvm.class_parser import (CONSTANT_Class, CONSTANT_Integer, CONSTANT_Methodref, CONSTANT_NameAndType, CONSTANT_String, Code,
                                     ClassFile,
                                     Method,
                                     CONSTANT_Utf8,
                                     CONSTANT_Fieldref,
                                     read_classfile)
import logging
import glob
from python_jvm.util import hexdump, parse_arg_num, parse_int

std_method = {
    'java/lang/System': {
        'out': {
            'println': lambda x: print(x[0])
        }
    }
}


def find_method(cfs: Dict[str, ClassFile], _class: str, name: str) -> Optional[Method]:
    c = cfs[_class]
    for m in c.methods:
        cp_name: CONSTANT_Utf8 = c.constant_pool[m.name_index]
        assert isinstance(cp_name, CONSTANT_Utf8)
        if cp_name.info == name.encode():
            return m
    return None


def find_code(m: Method, cfs: Dict[str, ClassFile], _class: str) -> Optional[Code]:
    c = cfs[_class]
    for a in m.attribute_info:
        cp_name: CONSTANT_Utf8 = c.constant_pool[a.attribute_name_index]
        assert isinstance(cp_name, CONSTANT_Utf8)
        if cp_name.info == b'Code':
            return Code(a.info)
    return None


def load_classes(classpath: str) -> Dict[str, ClassFile]:
    files = glob.glob(classpath)
    ret = {}
    for f in files:
        cf = read_classfile(f)
        cp_class: CONSTANT_Class = cf.constant_pool[cf.this_class]
        cp_name_utf8: CONSTANT_Utf8 = cf.constant_pool[cp_class.name_index]
        class_name: str = cp_name_utf8.info.decode()
        ret[class_name] = cf
    return ret


def _merge_unsigned_bytes(byte1: int, byte2: int) -> int:
    return int.from_bytes((byte1 << 8 | byte2).to_bytes(2, byteorder='big'), signed=True, byteorder='big')


def _new_instance(cfs: Dict[str, ClassFile], _class: str) -> Dict:
    return {
        'name': None,
        'age': None
    }


def execute(code: Code, cfs: Dict[str, ClassFile], _class: str, local_variables, heap: Dict[Any, Any]):
    c = cfs[_class]
    with mmap.mmap(-1, len(code.code)) as mm:
        mm.write(code.code)
        mm.seek(0)

        stack: List[Any] = []
        heap: Dict[Any, Any] = heap if heap else {}

        while True:
            opcode: bytes = mm.read(1)

            logging.debug(dedent(f'''
            ########################
            current position {mm.tell() - 1}
            opcode {hexdump(opcode)}
            stack {stack}
            heap {heap}
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
            elif opcode == b'\x06':
                logging.info('OPCODE: iconst_3')
                stack.append(3)
            elif opcode == b'\x08':
                logging.info('OPCODE: iconst_5')
                stack.append(5)
            elif opcode == b'\x10':
                logging.info('OPCODE: bipush')
                val = parse_int(mm.read(1))
                stack.append(val)
            elif opcode == b'\x11':
                logging.info('OPCODE: sipush')
                byte1 = parse_int(mm.read(1))
                byte2 = parse_int(mm.read(1))
                value = int.from_bytes((byte1 << 8 | byte2).to_bytes(2, byteorder='big'), signed=True, byteorder='big')
                stack.append(value)
            elif opcode == b'\x12':
                logging.info('OPCODE: ldc')
                pool_index = parse_int(mm.read(1))
                symbol_name_index: Union[CONSTANT_String, CONSTANT_Integer] = c.constant_pool[pool_index]
                if isinstance(symbol_name_index, CONSTANT_String):
                    cp_str: CONSTANT_Utf8 = c.constant_pool[symbol_name_index.string_index]
                    string = cp_str.info.decode()
                    stack.append(string)
                elif isinstance(symbol_name_index, CONSTANT_Integer):
                    stack.append(symbol_name_index.value)
                else:
                    raise Exception(f'unexpected constant {symbol_name_index}')
            elif opcode == b'\x15':
                logging.info('OPCODE: iload')
                index = parse_int(mm.read(1))
                stack.append(local_variables[index])
            elif opcode == b'\x1a':
                logging.info('OPCODE: iload_0')
                stack.append(local_variables[0])
            elif opcode == b'\x1b':
                logging.info('OPCODE: iload_1')
                stack.append(local_variables[1])
            elif opcode == b'\x1c':
                logging.info('OPCODE: iload_2')
                stack.append(local_variables[2])
            elif opcode == b'\x1d':
                logging.info('OPCODE: iload_3')
                stack.append(local_variables[3])
            elif opcode == b'\x2a':
                logging.info('OPCODE: aload_0')
                stack.append(local_variables[0])
            elif opcode == b'\x2b':
                logging.info('OPCODE: aload_1')
                stack.append(local_variables[1])
            elif opcode == b'\x36':
                logging.info('OPCODE: istore')
                val = stack.pop()
                index = parse_int(mm.read(1))
                local_variables[index] = val
            elif opcode == b'\x3c':
                logging.info('OPCODE: istore_1')
                local_variables[1] = stack.pop()
            elif opcode == b'\x3d':
                logging.info('OPCODE: istore_2')
                local_variables[2] = stack.pop()
            elif opcode == b'\x3e':
                logging.info('OPCODE: istore_3')
                local_variables[3] = stack.pop()
            elif opcode == b'\x59':
                logging.info('OPCODE: dup')
                val = stack.pop()
                copy_val = copy.deepcopy(val)
                stack.append(copy_val)
            elif opcode == b'\x60':
                logging.info('OPCODE: iadd')
                val1 = stack.pop()
                val2 = stack.pop()
                logging.debug(f"iadd {val1} + {val2}")
                stack.append(val1 + val2)
            elif opcode == b'\x64':
                logging.info('OPCODE: isub')
                value2 = stack.pop()
                value1 = stack.pop()
                stack.append(value1 - value2)
            elif opcode == b'\x84':
                logging.info('OPCODE: iinc')
                target = parse_int(mm.read(1))
                val = parse_int(mm.read(1))
                local_variables[target] += val
            elif opcode == b'\x9a':
                logging.info('OPCODE: ifne')
                branch1 = parse_int(mm.read(1))
                branch2 = parse_int(mm.read(1))
                value = stack.pop()
                if value != 0:
                    offset = int.from_bytes((branch1 << 8 | branch2).to_bytes(2, byteorder='big'), signed=True, byteorder='big') - 3
                    logging.debug(f'seek to {offset}')
                    mm.seek(offset, 1)
            elif opcode == b'\xa0':
                logging.info('OPCODE: if_icmpne')
                branch1 = parse_int(mm.read(1))
                branch2 = parse_int(mm.read(1))
                value2 = stack.pop()
                value1 = stack.pop()
                logging.debug(f'value1: {value1} value2: {value2}')
                if value1 != value2:
                    offset = int.from_bytes((branch1 << 8 | branch2).to_bytes(2, byteorder='big'), signed=True, byteorder='big') - 3
                    logging.debug(f'seek to {offset}')
                    mm.seek(offset, 1)

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
            elif opcode == b'\xac':
                logging.info('OPCODE: ireturn')
                return stack.pop()
            elif opcode == b'\xb2':
                logging.info('OPCODE: getstatic')
                pool_index = parse_int(mm.read(2))
                symbol_name: CONSTANT_Fieldref = c.constant_pool[pool_index]
                assert isinstance(symbol_name, CONSTANT_Fieldref)
                cp_class_callee: CONSTANT_Class = c.constant_pool[symbol_name.class_index]
                cp_class_callee_name: CONSTANT_Utf8 = c.constant_pool[cp_class_callee.name_index]
                callee_class: str = cp_class_callee_name.info.decode()

                cp_method_name_type: CONSTANT_NameAndType = c.constant_pool[symbol_name.name_and_type_index]
                cp_method_name: CONSTANT_Utf8 = c.constant_pool[cp_method_name_type.name_index]
                field: str = cp_method_name.info.decode()

                cp_method_descriptor: CONSTANT_Utf8 = c.constant_pool[cp_method_name_type.descriptor_index]
                method_return: str = cp_method_descriptor.info.decode()
                logging.debug(f'callee info, {callee_class}, {field}, {method_return}')

                # TODO
                stack.append({
                    'callable': {
                        'class': callee_class,
                        'field': field,
                        'return': method_return
                    }
                })
            elif opcode == b'\xb1':
                logging.info('OPCODE: return')
                return
            elif opcode == b'\xb5':
                logging.info('OPCODE: putfield')
                indexbyte1 = parse_int(mm.read(1))
                indexbyte2 = parse_int(mm.read(1))
                cp_field_ref_index = _merge_unsigned_bytes(indexbyte1, indexbyte2)
                cp_field_ref: CONSTANT_Fieldref = c.constant_pool[cp_field_ref_index]
                cp_field_name_type: CONSTANT_NameAndType = c.constant_pool[cp_field_ref.name_and_type_index]
                cp_field_name_utf8: CONSTANT_Utf8 = c.constant_pool[cp_field_name_type.name_index]
                cp_field_name: str = cp_field_name_utf8.info.decode()

                value = stack.pop()
                heap_id = stack.pop()
                logging.debug(f'cp_field_name: {cp_field_name} heap_id:{heap_id} value:{value}')
                heap[heap_id][cp_field_name] = value

            elif opcode == b'\xb6':
                logging.info('OPCODE: invokevirtual')
                pool_index = parse_int(mm.read(2))
                symbol_name_index = c.constant_pool[pool_index]

                callee = c.constant_pool[symbol_name_index.name_and_type_index]
                callee_method = c.constant_pool[callee.name_index].info.decode()  # println
                args_exp = c.constant_pool[callee.descriptor_index].info.decode()

                logging.debug(f'args_exp: {args_exp}')
                args = []
                # for _ in range(len(args_exp.split(';'))-1):
                for _ in range(1):
                    args.append(stack.pop())
                method = stack.pop()
                logging.debug(f'method: {method} args: {args}')

                std_method[method['callable']['class']][method['callable']['field']][callee_method](args[::-1])
                return_value = 'aaa'
            elif opcode == b'\xb7':
                logging.info('OPCODE: invokespecial')
                indexbyte1 = parse_int(mm.read(1))
                indexbyte2 = parse_int(mm.read(1))
                cp_callee_index = _merge_unsigned_bytes(indexbyte1, indexbyte2)

                cp_callee: CONSTANT_Methodref = c.constant_pool[cp_callee_index]
                cp_callee_class: CONSTANT_Class = c.constant_pool[cp_callee.class_index]
                cp_callee_class_utf8: CONSTANT_Utf8 = c.constant_pool[cp_callee_class.name_index]
                callee_class: str = cp_callee_class_utf8.info.decode()

                cp_callee_method: CONSTANT_NameAndType = c.constant_pool[cp_callee.name_and_type_index]
                callee_method: str = c.constant_pool[cp_callee_method.name_index].info.decode()
                logging.debug(f'invokespecial {callee_class}.{callee_method}')

                # if callee_class == 'java/lang/Object' and callee_method == '<init>':
                #     pass  # TODO
                # else:
                callee_method_obj = find_method(cfs, callee_class, callee_method)
                assert callee_method_obj is not None, f"{callee_class}.{callee_method} not found"
                callee_code = find_code(callee_method_obj, cfs, callee_class)

                args = [None for _ in range(callee_code.max_locals)]
                callee_descriptor_exp = cfs[callee_class].constant_pool[callee_method_obj.descriptor_index].info.decode()
                n_args = parse_arg_num(callee_descriptor_exp)
                logging.debug(f'calee_descriptor {callee_descriptor_exp}, {n_args}')
                args[0] = stack.pop()  # object ref
                for i in range(n_args):
                    args[i + 1] = stack.pop()
                stack.append(execute(callee_code, cfs, callee_class, args[::-1], heap))

            elif opcode == b'\xb8':
                logging.info('OPCODE: invokestatic')
                indexbyte1 = parse_int(mm.read(1))
                indexbyte2 = parse_int(mm.read(1))
                logging.debug(f'indexbyte1 {indexbyte1} indexbyte2 {indexbyte2}')
                callee_cp_index = int.from_bytes((indexbyte1 << 8 | indexbyte2).to_bytes(2, byteorder='big'), signed=True, byteorder='big')
                logging.debug(f'callee_cp_index {callee_cp_index}')
                callee_class = c.constant_pool[c.constant_pool[c.constant_pool[callee_cp_index].class_index].name_index].info.decode()
                callee_method = c.constant_pool[c.constant_pool[c.constant_pool[callee_cp_index].name_and_type_index].name_index].info.decode()
                logging.debug(f'invokestatic {callee_class}.{callee_method}')

                callee_method_obj = find_method(cfs, callee_class, callee_method)
                assert callee_method_obj is not None, f"{callee_class}.{callee_method} not found"
                callee_code = find_code(callee_method_obj, cfs, callee_class)

                args = [None for _ in range(callee_code.max_locals)]
                callee_descriptor_exp = cfs[callee_class].constant_pool[callee_method_obj.descriptor_index].info.decode()
                n_args = 1 if '(I)' in callee_descriptor_exp else 2 if '(II)' in callee_descriptor_exp else 0
                for i in range(n_args):
                    args[i] = stack.pop()

                stack.append(execute(callee_code, cfs, callee_class, args, {}))
            elif opcode == b'\xbb':
                logging.info('OPCODE: new')
                indexbyte1 = parse_int(mm.read(1))
                indexbyte2 = parse_int(mm.read(1))
                target_class_index = _merge_unsigned_bytes(indexbyte1, indexbyte2)
                cp_class: CONSTANT_Class = c.constant_pool[target_class_index]
                cp_class_utf8: CONSTANT_Utf8 = c.constant_pool[cp_class.name_index]
                class_name: str = cp_class_utf8.info.decode()
                logging.debug(f"new class #{target_class_index} {class_name}")

                heap[len(heap)] = _new_instance(cfs, class_name)
                heap_index = len(heap) - 1
                stack.append(heap_index)

            else:
                raise Exception(f'unknown opcode {opcode}')
