from python_jvm.executer import find_code, load_classes, find_method, execute
import logging
logging.basicConfig(
    # encoding='utf-8',
    level=logging.DEBUG)


cfs = load_classes('./HelloWorld.class')
main_method = find_method(cfs, 'HelloWorld', 'main')
assert main_method is not None
main_method_code = find_code(main_method, cfs, 'HelloWorld')
execute(main_method_code, cfs, 'HelloWorld', [None for _ in range(main_method_code.max_locals)], {})
