from importlib import (
    util,
)  # https://stackoverflow.com/questions/39660934/error-when-using-importlib-util-to-check-for-library
from math import isnan
from types import ModuleType, FunctionType
from typing import Any, Dict, List

import arepl_jsonpickle as jsonpickle
from arepl_custom_handlers import handlers

#####################################
"""
This file sets up jsonpickle. Jsonpickle is used in pickle_user_vars for picking user variables.
"""
#####################################


class CustomPickler(jsonpickle.pickler.Pickler):
    """
    encodes float values like inf / nan as strings to follow JSON spec while keeping meaning
    Im doing this in custom class because handlers do not fire for floats
    """

    inf = float("inf")
    negativeInf = float("-inf")

    def _flatten(self, obj):
        if type(obj) == float:
            if obj == self.inf:
                return "Infinity"
            if obj == self.negativeInf:
                return "-Infinity"
            if isnan(obj):
                return "NaN"
        return super(CustomPickler, self)._flatten(obj)


if util.find_spec("numpy") is not None:
    try:
        import arepl_jsonpickle.ext.numpy as jsonpickle_numpy

        jsonpickle_numpy.register_handlers()
    except ImportError:
        # todo: log ImportError
        pass

if util.find_spec("pandas") is not None:
    try:
        import arepl_jsonpickle.ext.pandas as jsonpickle_pandas

        jsonpickle_pandas.register_handlers()
    except ImportError:
        # todo: log ImportError
        pass

jsonpickle.pickler.Pickler = CustomPickler
jsonpickle.set_encoder_options("json", ensure_ascii=False)
jsonpickle.set_encoder_options("json", allow_nan=False)  # nan is not deseriazable by javascript
for handler in handlers:
    jsonpickle.handlers.register(handler["type"], handler["handler"])

specialVars = ["__doc__", "__file__", "__loader__", "__name__", "__package__", "__spec__", "arepl_store"]


def pickle_user_vars(
    userVars: Dict[str, Any],
    default_filter_vars: List[str] = [],
    default_filter_types: List[str] = ["<class 'module'>", "<class 'function'>"],
):

    default_filter_vars += userVars.get("arepl_filter", [])
    default_filter_types += userVars.get("arepl_filter_type", [])
    custom_filter_function = userVars.get("arepl_filter_function", lambda x: x)

    # filter out non-user vars, no point in showing them
    userVariables = {
        k: v
        for k, v in userVars.items()
        if str(type(v)) not in default_filter_types
        and k not in specialVars + ["__builtins__"]
        and k not in default_filter_vars
    }

    # These vars are just for filtering, no need to show to user
    userVariables.pop("arepl_filter", None)
    userVariables.pop("arepl_filter_type", None)
    userVariables.pop("arepl_filter_function", None)

    # but we do want to show arepl_store if it has data
    if userVars.get("arepl_store") is not None:
        userVariables["arepl_store"] = userVars["arepl_store"]

    userVariables = custom_filter_function(userVariables)

    # json dumps cant handle any object type, so we need to use jsonpickle
    # still has limitations but can handle much more
    return jsonpickle.encode(
        userVariables,
        max_depth=100,  # any depth above 245 resuls in error and anything above 100 takes too long to process
        fail_safe=lambda x: "AREPL could not pickle this object",
        make_refs=False,  # We set this to False for more human readable output - see #115
    )


def pickle_user_error(error):

    # error needs to have context/cause
    # as a actual attribute so it gets pickled
    originalError = error
    while error:
        if error.__context__:
            error.context = error.__context__
            error = error.__context__
        if error.__cause__:
            error.cause = error.__cause__
            error = error.__cause__
        if error.__cause__ is None and error.__context__ is None:
            break

    return jsonpickle.encode(originalError, fail_safe=lambda x: "AREPL could not pickle this object")
