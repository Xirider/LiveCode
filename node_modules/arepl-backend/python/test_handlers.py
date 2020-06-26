import arepl_jsonpickle as jsonpickle

import arepl_python_evaluator as python_evaluator


def test_frame_handler():
    # I have a custom handler for frame (see https://github.com/Almenon/AREPL-backend/issues/26)
    # otherwise frame returns as simply "py/object": "__builtin__.frame"
    frame_code = """
import bdb

f = {}

class areplDebug(bdb.Bdb):
    # override
    def user_line(self,frame):
        global f
        f = frame

b = areplDebug()
b.run('x=1+5',{},{})
    """
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(frame_code))
    vars = jsonpickle.decode(return_info.userVariables)
    assert vars["f"]["f_lineno"] == 1


def test_generator_handler():
    generator_code = """
def count(start=0):
    while True:
        yield start
        start += 1

counter = count()
    """
    return_info = python_evaluator.exec_input(python_evaluator.ExecArgs(generator_code))
    vars = jsonpickle.decode(return_info.userVariables)
    assert vars["counter"]["py/object"] == "builtins.generator"
