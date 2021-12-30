from _pytest.config import main
import pytest
from python_jvm.class_parser import read_classfile
from python_jvm.executer import execute, find_code, find_method

@pytest.fixture(params=[
    'HelloWorld.class',
    'Print.class'])
def classfile_path(request):
    return request.param

def test_some_classfile(classfile_path):
    '''Test it can parse all class file without Exception'''
    cf = read_classfile(classfile_path) 
    main_method = find_method(cf, 'main')
    if main_method:
        main_method_code = find_code(main_method, cf)
        execute(main_method_code, cf, [None for _ in range(main_method_code.max_locals)])
    