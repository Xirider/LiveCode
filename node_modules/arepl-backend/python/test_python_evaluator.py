from os import chdir, getcwd, listdir, path, pardir, remove
from sys import version_info, modules
from shutil import rmtree
import tempfile

import pytest
import arepl_jsonpickle as jsonpickle

import arepl_python_evaluator as python_evaluator
from arepl_settings import update_settings

python_ignore_path = path.join(path.dirname(path.abspath(__file__)), "testDataFiles")
# The frontend will pass in below settings as default
default_settings = {
    "showGlobalVars": True,
    "default_filter_vars": [],
    "default_filter_types": ["<class 'module'>", "<class 'function'>"],
}


def setup_function():
    update_settings(default_settings)


def test_simple_code():
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs("x = 1"))
    assert jsonpickle.decode(return_info.userVariables)["x"] == 1


def test_has_error():
    with pytest.raises(python_evaluator.UserError):
        python_evaluator.exec_input(python_evaluator.ExecArgs("x"))


def test_error_has_traceback():
    try:
        python_evaluator.exec_input(
            python_evaluator.ExecArgs(
                """
def foo():
    x
foo()
        """
            )
        )
    except (KeyboardInterrupt, SystemExit):
        raise
    except python_evaluator.UserError as e:
        assert e.traceback_exception.exc_type == NameError
        assert len(e.traceback_exception.stack) == 2
        assert e.traceback_exception.stack[0].lineno == 4
        assert e.traceback_exception.stack[1].lineno == 3
        assert "name 'x' is not defined" in e.friendly_message


def test_dict_unpack_error():
    with pytest.raises(python_evaluator.UserError):
        python_evaluator.exec_input(python_evaluator.ExecArgs("[(k,v) for (k,v) in {'a': 1}]"))
        

def test_main_returns_var():
    mock_stdin = """{
        "savedCode": "",
        "evalCode": "x=1",
        "filePath": "",
        "usePreviousVariables": false,
        "showGlobalVars": true
    }"""
    return_info = python_evaluator.main(mock_stdin)
    assert jsonpickle.decode(return_info.userVariables)["x"] == 1


def test_main_returns_var_even_when_error():
    mock_stdin = """{
        "savedCode": "",
        "evalCode": "y=1;x",
        "filePath": "",
        "usePreviousVariables": false,
        "showGlobalVars": true
    }"""
    return_info = python_evaluator.main(mock_stdin)
    assert jsonpickle.decode(return_info.userVariables)["y"] == 1


def test_infinite_generator():
    return_info = python_evaluator.exec_input(
        python_evaluator.ExecArgs(
            """
import itertools
counter = (x for x in itertools.count())
x=next(counter)
    """
        )
    )
    assert jsonpickle.decode(return_info.userVariables)["x"] == 0


def test_dont_show_global_vars():
    update_settings({"showGlobalVars": False})
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs("x = 1"))
    assert jsonpickle.decode(return_info.userVariables)["zz status"] == "AREPL is configured to not show global vars"


def test_argv0_should_be_file_path():
    code = "from sys import argv;args=argv"
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(code))
    assert jsonpickle.decode(return_info.userVariables)["args"][0] == ""

    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(code, "", filePath="test path"))
    assert jsonpickle.decode(return_info.userVariables)["args"][0] == "test path"


def test_syspath0_should_be_file_path():
    code = "from sys import path;first_path=path[0]"
    temp_dir = tempfile.gettempdir()
    fake_temp_file = path.join(temp_dir, "foo.py")
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(code, "", filePath=fake_temp_file))
    assert jsonpickle.decode(return_info.userVariables)["first_path"] == temp_dir


def test_starting_dunders_should_be_correct():
    code = "file_dunder=__file__"
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(code))
    assert jsonpickle.decode(return_info.userVariables)["file_dunder"] == ""

    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(code, "", filePath="test path"))
    assert jsonpickle.decode(return_info.userVariables)["file_dunder"] == "test path"

    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs("name_dunder=__name__"))
    assert jsonpickle.decode(return_info.userVariables)["name_dunder"] == "__main__"

    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs("loader_dunder=__loader__", filePath="test path"))
    assert jsonpickle.decode(return_info.userVariables)["loader_dunder"].name == "__main__"

    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs("loader_dunder=__loader__", filePath="test path"))
    assert jsonpickle.decode(return_info.userVariables)["loader_dunder"].path == "test path"


def test_relative_import():
    file_path = path.join(python_ignore_path, "foo2.py")
    with open(file_path) as f:
        return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(f.read(), "", file_path))
    assert jsonpickle.decode(return_info.userVariables)["x"] == 2


def test_dump():
    return_info = python_evaluator.exec_input(
        python_evaluator.ExecArgs("from arepl_dump import dump;dump('dump worked');x=1")
    )
    assert jsonpickle.decode(return_info.userVariables)["x"] == 1


def test_dump_when_exception():
    # this test prevents rather specific error case where i forget to uncache dump during exception handling
    # and it causes dump to not work properly second time around (see https://github.com/Almenon/AREPL-vscode/issues/91)
    try:
        python_evaluator.exec_input(
            python_evaluator.ExecArgs("from arepl_dump import dump;dumpOut = dump('dump worked');x=1;raise Exception()")
        )
    except Exception as e:
        assert "dumpOut" in jsonpickle.decode(e.varsSoFar)
    try:
        python_evaluator.exec_input(
            python_evaluator.ExecArgs("from arepl_dump import dump;dumpOut = dump('dump worked');raise Exception()")
        )
    except Exception as e:
        assert "dumpOut" in jsonpickle.decode(e.varsSoFar) and jsonpickle.decode(e.varsSoFar)["dumpOut"] is not None


def test_import_does_not_show():
    # we only show local vars to user, no point in showing modules
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs("import json"))
    assert jsonpickle.decode(return_info.userVariables) == {}


def test_save():
    return_info = python_evaluator.exec_input(
        python_evaluator.ExecArgs("", "from random import random\nx=random()#$save")
    )
    randomVal = jsonpickle.decode(return_info.userVariables)["x"]
    return_info = python_evaluator.exec_input(
        python_evaluator.ExecArgs("z=3", "from random import random\nx=random()#$save")
    )
    assert jsonpickle.decode(return_info.userVariables)["x"] == randomVal


def test_save_import():  # imports in saved section should be able to be referenced in exec section
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs("z=math.sin(0)", "import math#$save"))
    assert jsonpickle.decode(return_info.userVariables)["z"] == 0


def test_various_types():
    various_types = """
a = 1
b = 1.1
c = 'c'
d = (1,2)
def f(x): return x+1
g = {}
h = []
i = [[[]]]
class l():
    def __init__(self,x):
        self.x = x
m = l(5)
n = False

    """
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(various_types))

    vars = jsonpickle.decode(return_info.userVariables)
    assert vars["a"] == 1
    assert vars["b"] == 1.1
    assert vars["c"] == "c"
    assert vars["d"] == (1, 2)
    assert vars["g"] == {}
    assert vars["h"] == []
    assert vars["i"] == [[[]]]
    assert vars["l"] != None
    assert vars["m"] != None
    assert vars["n"] == False


def test_file_IO():
    file_IO = """
import tempfile

fp = tempfile.TemporaryFile()
fp.write(b'yo')
fp.seek(0)
x = fp.read()
fp.close()
    """
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(file_IO))
    vars = jsonpickle.decode(return_info.userVariables)
    assert "fp" in vars
    assert vars["x"] == b"yo"


def test_event_Loop():
    event_loop_code = """
import asyncio

async def async_run():
    pass

def compile_async_tasks():
    tasks = []

    tasks.append(
        asyncio.ensure_future(async_run())
    )
    return tasks

tasks = compile_async_tasks()

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(*tasks))
loop.close()
x=1
    """

    # the async def async_run would result
    # in syntax error in python versions < 3.5
    # so we use different test in that case
    if version_info < (3, 5):
        event_loop_code = """
import asyncio

@asyncio.coroutine
def hello_world():
    print("Hello World!")

loop = asyncio.get_event_loop()
# Blocking call which returns when the hello_world() coroutine is done
loop.run_until_complete(hello_world())
loop.close()
x=1
    """

    python_evaluator.exec_input(python_evaluator.ExecArgs(event_loop_code))
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(event_loop_code))
    vars = jsonpickle.decode(return_info.userVariables)
    assert "x" in vars


def test_builtinImportNotDeleted():
    importStr = """
import math
from json import loads
    """
    python_evaluator.exec_input(python_evaluator.ExecArgs(importStr))
    assert "math" in modules
    assert "json" in modules


def test_pipImportNotDeleted():
    importStr = """
import praw
    """
    python_evaluator.exec_input(python_evaluator.ExecArgs(importStr))
    assert "praw" in modules
    assert "praw.models.user" in modules


def test_user_import_deleted():

    file_path = path.join(python_ignore_path, "foo.py")
    file_path2 = path.join(python_ignore_path, "foo2.py")

    with open(file_path) as f:
        origFileText = f.read()

    try:
        with open(file_path2) as f:
            return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(f.read(), "", file_path2))
        assert jsonpickle.decode(return_info.userVariables)["x"] == 2  # just checking this for later on
        assert "foo" not in modules  # user import should be deleted!

        # now that import is uncached i should be able to change code, rerun & get different result
        with open(file_path, "w") as f:
            f.write("def foo():\n    return 3")

        with open(file_path2) as f:
            return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(f.read(), "", file_path2))
        assert jsonpickle.decode(return_info.userVariables)["x"] == 3

    finally:
        # restore file back to original
        with open(file_path, "w") as f:
            f.write(origFileText)


def test_user_var_import_deleted():

    # __pycache__ will muck up our test on every second run
    # this problem only happens during unit tests and not in actual useage (not sure why)
    # so we can safely delete pycache to avoid the problem
    rmtree(path.join(python_ignore_path, "__pycache__"))

    varToImportFile_path = path.join(python_ignore_path, "varToImport.py")
    importVarFile_path = path.join(python_ignore_path, "importVar.py")

    with open(varToImportFile_path) as f:
        origVarToImportFileText = f.read()

    try:
        with open(importVarFile_path) as f:
            return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(f.read(), "", importVarFile_path))
        assert jsonpickle.decode(return_info.userVariables)["myVar"] == 5  # just checking this for later on
        assert "varToImport" not in modules  # user import should be deleted!

        # now that import is uncached i should be able to change code, rerun & get different result
        with open(varToImportFile_path, "w") as f:
            f.write("varToImport = 3")

        with open(importVarFile_path) as f:
            return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(f.read(), "", importVarFile_path))
        assert jsonpickle.decode(return_info.userVariables)["myVar"] == 3

    finally:
        # restore file back to original
        with open(varToImportFile_path, "w") as f:
            f.write(origVarToImportFileText)


def test_arepl_store():
    python_evaluator.exec_input(python_evaluator.ExecArgs("arepl_store=5"))
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs("x=arepl_store"))
    assert jsonpickle.decode(return_info.userVariables)["x"] == 5


def test_howdoiArepl():
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs("x=howdoi('use arepl')"))
    assert (
        jsonpickle.decode(return_info.userVariables)["x"]
        == "using AREPL is simple - just start coding and arepl will show you the final state of your variables. For more help see https://github.com/Almenon/AREPL-vscode/wiki"
    )


def test_script_path_should_work_regardless_of_user_errors():
    try:
        python_evaluator.exec_input(python_evaluator.ExecArgs("from sys import path;x", filePath=python_ignore_path))
    except python_evaluator.UserError as e:
        return_info = e.varsSoFar
    try:
        python_evaluator.exec_input(python_evaluator.ExecArgs("from sys import path;x", filePath=python_ignore_path))
    except python_evaluator.UserError as e:
        secondreturn_info = e.varsSoFar

    # script_path should restore the sys path back to original state after execution
    # so each run should have same path
    assert jsonpickle.decode(return_info)["path"] == jsonpickle.decode(secondreturn_info)["path"]


def test_mock_stdin():
    return_info = python_evaluator.exec_input(
        python_evaluator.ExecArgs("standard_input = 'hello\\nworld';x=input();y=input()")
    )
    assert jsonpickle.decode(return_info.userVariables)["x"] == "hello"
    assert jsonpickle.decode(return_info.userVariables)["y"] == "world"

    return_info = python_evaluator.exec_input(
        python_evaluator.ExecArgs("standard_input = ['hello', 'world'];x=input();y=input()")
    )
    assert jsonpickle.decode(return_info.userVariables)["x"] == "hello"
    assert jsonpickle.decode(return_info.userVariables)["y"] == "world"

    with pytest.raises(python_evaluator.UserError):
        python_evaluator.exec_input(python_evaluator.ExecArgs("standard_input = ['hello'];x=input();y=input()"))


def integration_test_howdoi():
    # this requires internet access so it is not official test
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs("x=howdoi('eat a apple')"))
    print(jsonpickle.decode(return_info.userVariables)["x"])  # this should print out howdoi results


###########################
#     WIERD STUFF
###########################

# lambdas do not show up at all

# file objects show up as None

#   class pickling does work with #$save - but not when unit testing for some reason
#   "Can't pickle <class 'python_evaluator.l'>: it's not found as python_evaluator.l"
#   not sure why it's trying to find the class in python_evaluator - it's not going to be there
#   todo: investigate issue

#    def test_can_pickle_class(self):
#         code = """
# class l():
# 	def __init__(self,x):
# 		self.x = x  #$save"""
#         return_info = python_evaluator.exec_input(python_evaluator.ExecArgs("",code))
#         randomVal = jsonpickle.decode(return_info['userVariables'])['l']
#         return_info = python_evaluator.exec_input(python_evaluator.ExecArgs("z=3",code))
#         randomVal = jsonpickle.decode(return_info['userVariables'])['l']
