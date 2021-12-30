from _pytest.config import main
import pytest
from python_jvm.class_parser import read_classfile
from python_jvm.executer import execute, find_code, find_method
import subprocess

@pytest.fixture(params=[
    'HelloWorld.class',
    'Print.class'])
def classfile_path(request):
    return request.param

def test_read_classfile(classfile_path):
    '''Test it can parse all class file without Exception'''
    read_classfile(classfile_path) 

stdout = ""
def test_execute_classfile(classfile_path, mocker):
    global stdout
    cf = read_classfile(classfile_path) 
    main_method = find_method(cf, 'main')

    stdout = ""
    def append_stdout(text):
        global stdout
        stdout += str(text) + "\n"
    if main_method:
        mocker.patch("python_jvm.executer.std_method", {
            'java/lang/System': {
                'out':{
                    'println': lambda x:append_stdout(x[0]) 
                }
            }
        })
        target_class = ''.join(classfile_path.split('.')[:-1])
        expected = subprocess.check_output(
            f'java -cp . {target_class}',
            shell=True, 
            # stderr=subprocess.STDOUT,
            cwd='.').decode()
        main_method_code = find_code(main_method, cf)
        execute(main_method_code, cf, [None for _ in range(main_method_code.max_locals)])
        assert stdout == expected
    

