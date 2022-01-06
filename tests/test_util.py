import pytest
from python_jvm.util import parse_arg_num


@pytest.mark.parametrize('descriptor, expected', [
    ('(I)I', 1),  # 1 arg, 1 return
    ('(II)I', 2),  # 2 arg, 1 return
    ('()V', 0),  # no arg, void return
    ('()I', 0),  # no arg, 1 int return
    ('([Ljava/lang/String;)V', 1),  # 1 arg, void return
    ('([Ljava/lang/String;Ljava/lang/String;)V', 2),  # 2 arg, void return
    ('([I)V', 1),  # 1 array arg, void return
    ('([I[I)V', 2),  # 2 array arg, void return
    ('(Ljava/lang/String;I)V', 2)
])
def test_parse_arg_num(descriptor, expected):
    '''
    see https://docs.oracle.com/javase/specs/jvms/se8/html/jvms-4.html#jvms-4.3
    '''
    assert parse_arg_num(descriptor) == expected
