from _pytest.config import main
import pytest
from python_jvm.class_parser import read_classfile
from python_jvm.executer import execute, find_code, find_method, load_classes
import subprocess


@pytest.fixture(params=[
    './tests/java/HelloWorld.class',
    # 'Print.class'
])
def classfile_path(request):
    return request.param


def test_read_classfile(classfile_path):
    '''Test it can parse all class file without Exception'''
    read_classfile(classfile_path)


def test_load_classes():
    actual = load_classes('./tests/java/*.class')
    assert actual.keys() == {"HelloWorld", "Print", "java/lang/Object", "Person"}


stdout = ""


def test_execute_classfile(classfile_path, mocker):
    global stdout
    cfs = load_classes('./tests/java/*.class')
    cf = read_classfile(classfile_path)
    main_method = find_method(cfs, 'HelloWorld', 'main')

    stdout = ""

    def append_stdout(text):
        global stdout
        stdout += str(text) + "\n"
    if main_method:
        mocker.patch("python_jvm.executer.std_method", {
            'java/io/PrintStream': {
                'println': lambda x: append_stdout(x[0])
            }
        })
        target_class = ''.join(classfile_path.split('.')[:-1]).split('/')[-1]
        expected = subprocess.check_output(
            f'cd ./tests/java; java -cp . {target_class}',
            shell=True,
            # stderr=subprocess.STDOUT,
            cwd='.').decode()
        main_method_code = find_code(main_method, cfs, 'HelloWorld')
        execute(main_method_code, cfs, 'HelloWorld', [None for _ in range(main_method_code.max_locals)], {})
        assert stdout == expected
