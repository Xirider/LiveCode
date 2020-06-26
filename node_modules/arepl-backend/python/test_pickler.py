from arepl_pickler import specialVars, pickle_user_vars, pickle_user_error
import arepl_python_evaluator as python_evaluator
import arepl_jsonpickle as jsonpickle


def test_special_floats():
    x = float("infinity")
    y = float("nan")
    z = float("-infinity")
    vars = jsonpickle.decode(pickle_user_vars(locals()))
    assert vars["x"] == "Infinity"
    assert vars["y"] == "NaN"
    assert vars["z"] == "-Infinity"


def test_default_type_filter():
    def foo():
        return 3

    cat = 2
    vars = jsonpickle.decode(pickle_user_vars(locals()))

    assert vars["cat"] == 2
    assert "foo" not in vars


def test_custom_filter():
    arepl_filter = ["dog"]
    dog = 1
    cat = 2
    vars = jsonpickle.decode(pickle_user_vars(locals()))

    assert vars["cat"] == 2
    assert "dog" not in vars
    assert "arepl_filter" not in vars


def test_custom_type_filter():
    arepl_filter_type = ["<class 'str'>"]
    dog = ""
    cat = 2
    vars = jsonpickle.decode(pickle_user_vars(locals()))

    assert vars["cat"] == 2
    assert "dog" not in vars
    assert "arepl_filter_type" not in vars


def test_custom_filter_function():
    def arepl_filter_function(userVariables):
        userVariables["a"] = 3
        return userVariables

    vars = jsonpickle.decode(pickle_user_vars(locals()))

    assert vars["a"] == 3
    assert "arepl_filter_function" not in vars


def test_jsonpickle_err_doesnt_break_arepl():
    class foo:
        def __getstate__(self):
            a

    f = foo()

    assert jsonpickle.decode(pickle_user_vars(locals()))["f"] == "AREPL could not pickle this object"


# I don't want to require pandas to run tests
# So leaving this commented, devs can uncomment to run test if they want to
# def test_jsonpickle_err_doesnt_break_arepl_2():
#     import pandas as pd
#     lets = ['A', 'B', 'C']
#     nums = ['1', '2', '3']
#     midx = pd.MultiIndex.from_product([lets, nums])
#     units = pd.Series(0, index=midx)

#     assert jsonpickle.decode(pickle_user_vars(locals()))["units"] == "AREPL could not pickle this object"


def test_error_has_extended_traceback_1():
    try:
        python_evaluator.exec_input(
            python_evaluator.ExecArgs(
                """
try:
    x
except NameError as e:
    x=1/0
"""
            )
        )
    except (KeyboardInterrupt, SystemExit):
        raise
    except python_evaluator.UserError as e:
        json = pickle_user_error(e.traceback_exception)
        assert "ZeroDivisionError" in json
        assert "NameError" in json


def test_error_has_extended_traceback_2():
    try:
        python_evaluator.exec_input(
            python_evaluator.ExecArgs(
                """
def foo():
    raise ZeroDivisionError()
    
try:
    foo()
except Exception as e:
    fah
"""
            )
        )
    except (KeyboardInterrupt, SystemExit):
        raise
    except python_evaluator.UserError as e:
        json = pickle_user_error(e.traceback_exception)
        assert "NameError" in json
        assert "ZeroDivisionError" in json
