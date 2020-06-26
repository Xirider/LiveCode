import arepl_jsonpickle
import inspect
import json
from time import time
from typing import Any, List, Union
from arepl_python_evaluator import pickle_user_vars, ReturnInfo, print_output
from arepl_settings import get_settings

context = {}


def dump(variable: Any = None, atCount: Union[int, List[int]] = 0):
    """
    dumps specified var to arepl viewer or all vars of calling scope if unspecified
    :param atCount: when to dump. ex: dump(,3) to dump vars at fourth iteration of loop. You can pass in a list of numbers to do multiple dumps.
    """
    startTime = time()

    callingFrame = inspect.currentframe().f_back

    callerFile = callingFrame.f_code.co_filename
    callerLine = callingFrame.f_lineno
    caller = callingFrame.f_code.co_name
    key = callerFile + caller + str(callerLine)

    count = 0

    try:
        count = context[key] + 1
    except KeyError:
        pass

    context[key] = count

    if count == atCount or (type(atCount) is list and count in atCount):
        if variable is None:
            variableDict = callingFrame.f_locals
        else:
            variableDict = {"dump output": variable}

        variableJson = pickle_user_vars(
            variableDict, get_settings().default_filter_vars, get_settings().default_filter_types
        )
        my_return_info = ReturnInfo(
            "", variableJson, None, time() - startTime, None, caller, callerLine, done=False, count=count
        )

        print_output(my_return_info)

        # we don't need to return anything for user, this is just to make testing easier
        return my_return_info


# dump(5) for quick testing
