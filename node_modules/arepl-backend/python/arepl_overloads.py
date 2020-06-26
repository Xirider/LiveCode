import inspect
from typing import Any

"""
This file contains overloads of certain python functions for arepl purposes
For example, arepl doesn't support stdin so we overload input and help
"""

# AREPL-vscode does not support stdin yet so help breaks it
# by overridding help with a non-stdin version we can prevent AREPL-vscode from freezing up
# just a temp fix untill AREPL-vscode supports stdin
def help_overload(arg: Any = None):
    if arg is None:
        print(
            """Welcome to python! :)
If this is your first time using Python, you should definitely check out
the tutorial on the Internet at https://docs.python.org/3.7/tutorial/.

AREPL uses a custom implementation of help which does not have all the features of the interpreter help. 
But AREPL's help can still give you information on functions / modules / objects you pass into it."""
        )
    else:
        print(arg.__doc__)


arepl_input_iterator = None

# AREPL doesn't support input so we overload input
# This allows users to hardcode input by specifying a standard_input var
def input_overload(prompt: str = None) -> str:
    """AREPL requires standard_input to be hardcoded, like so: standard_input = 'hello world'; print(input()). You can also hardcode standard_input as a generator or list.
    
    Keyword Arguments:
        prompt {str} --  (default: {None})
    
    Raises:
        StopIteration -- if there is no more input
    """
    global arepl_input_iterator

    if prompt is not None:
        print(prompt)
    try:
        if arepl_input_iterator is not None:
            try:
                return next(arepl_input_iterator)
            except StopIteration:
                # give simple user-friendly error, we dont want users worry about error in arepl source code
                raise StopIteration("There is no more input") from None
        else:

            callingFrame = inspect.currentframe().f_back
            standard_input = callingFrame.f_globals["standard_input"]

            if type(standard_input) is str:
                arepl_input_iterator = iter([line for line in standard_input.split("\n")])
            elif callable(standard_input):
                arepl_input_iterator = standard_input()
            else:
                arepl_input_iterator = iter([line for line in standard_input])

            return next(arepl_input_iterator)
    except KeyError:
        print("AREPL requires standard_input to be hardcoded, like so: standard_input = 'hello world'; print(input())")
        return ""


def howdoi_wrapper(query: str) -> str:
    """howdoi is meant to be called from the command line - this wrapper lets it be called programatically
    
    Arguments:
        query {str} -- search term
    """

    if query.lower() == "use arepl" or query.lower() == "arepl":
        returnVal = "using AREPL is simple - just start coding and arepl will show you the final state of your variables. For more help see https://github.com/Almenon/AREPL-vscode/wiki"
    else:
        try:
            parser = howdoi.get_parser()
        except NameError as e:
            # alter error to be more readable by user
            e.args = ("howdoi is not installed",)
            raise

        args = vars(parser.parse_args(query.split(" ")))
        returnVal = howdoi.howdoi(args)

    print(returnVal)
    return returnVal  # not actually necessary but nice for unit testing
