import pytest
from python_jvm.class_parser import read_classfile

@pytest.fixture(params=[
    'HelloWorld.class',
    'Print.class'])
def classfile_path(request):
    return request.param

def test_some_classfile(classfile_path):
    '''Test it can parse all class file without Exception'''
    read_classfile(classfile_path) 