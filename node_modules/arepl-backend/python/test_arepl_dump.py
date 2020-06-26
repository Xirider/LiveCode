import pytest
from json import loads

from arepl_dump import dump

# this test has to be in main scope
# so we cant run it inside a function
output = dump(5)


def test_simple_dump():
    dumpInfo = dump("yo")
    assert loads(dumpInfo.userVariables)["dump output"] == "yo"
    assert dumpInfo.caller == "test_simple_dump"
    assert dumpInfo.done == False


def test_dump_main_scope():
    global output
    assert loads(output.userVariables)["dump output"] == 5
    assert output.caller == "<module>"


def test_dump_all_vars():
    y = "hey"
    dumpInfo = dump()
    assert loads(dumpInfo.userVariables)["y"] == "hey"


def test_dump_at():
    for i in range(10):
        output = dump("yo")
        output2 = dump(i, 3)
        if i is 0:
            output = output
            assert loads(output.userVariables)["dump output"] == "yo"
        elif i is 3:
            output2 = output2
            assert loads(output2.userVariables)["dump output"] == 3
        else:
            assert output is None


def test_dump_at_list():
    for i in range(10):
        output = dump(i, [2, 3])
        if i is 2:
            output = output
            assert loads(output.userVariables)["dump output"] == 2
        elif i is 3:
            output = output
            assert loads(output.userVariables)["dump output"] == 3
        else:
            assert output is None
