import ast
from copy import deepcopy
import traceback
from arepl_pickler import pickle_user_vars, specialVars
from arepl_user_error import UserError
from sys import exc_info
from typing import Any, Dict, List

#####################################
"""
This file contains code for getting the saved or starting local variables for each run
Idea is user can optionally have a block of "saved" code that will retain vars each run
In practice not sure if this is actually used and its quite buggy :(
"""
#####################################

saved_locals = {}
old_saved_lines = ""
starting_locals = {}

# public cache var for user to store their data between runs
arepl_store = None

# copy all special vars (we want execd code to have similar locals as actual code)
# not copying builtins cause exec adds it in
# also when specialVars is deepCopied later on deepcopy cant handle builtins anyways
for var in specialVars:
    starting_locals[var] = locals()[var]

# users code should execute under main scope
starting_locals["__name__"] = "__main__"
starting_locals["__loader__"].name = "__main__"

# spec should not exist when executing file directly
del starting_locals["__spec__"]


def get_starting_locals() -> Dict[str, Any]:
    starting_locals_copy = deepcopy(starting_locals)
    starting_locals_copy["arepl_store"] = arepl_store
    return starting_locals_copy


def exec_saved(savedLines: str) -> Dict[str, Any]:
    saved_locals = get_starting_locals()
    try:
        exec(savedLines, saved_locals)
    except Exception:
        _, exc_obj, exc_tb = exc_info()
        raise UserError(exc_obj, exc_tb, saved_locals)

    # deepcopy cant handle imported modules, so remove them
    saved_locals = {k: v for k, v in saved_locals.items() if str(type(v)) != "<class 'module'>"}

    return saved_locals


def get_eval_locals(savedLines: str) -> Dict[str, Any]:
    """
    If savedLines is changed, rexecutes saved lines and returns resulting local variables.
    If savedLines is unchanged, returns the saved locals.
    If savedLines is empty, simply returns the original starting_locals.
    """
    global old_saved_lines
    global saved_locals

    # "saved" code we only ever run once and save locals, vs. codeToExec which we exec as the user types
    # although if saved code has changed we need to re-run it
    if savedLines != old_saved_lines:
        saved_locals = exec_saved(savedLines)
        old_saved_lines = savedLines

    if savedLines != "":
        return deepcopy(saved_locals)
    else:
        return get_starting_locals()


def get_imports(parsedText: ast.AST, text: str) -> str:
    """
    :param parsedText: the result of ast.parse(text)
    :returns: empty string if no imports, otherwise string containing all imports
    """

    child_nodes = [l for l in ast.iter_child_nodes(parsedText)]

    imports = []
    saved_code = text.split("\n")
    for node in child_nodes:
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            importLine = saved_code[node.lineno - 1]
            imports.append(importLine)

    imports = "\n".join(imports)
    return imports


def copy_saved_imports_to_exec(codeToExec: str, savedLines: str) -> str:
    """
    copies imports in savedLines to the top of codeToExec.
    If savedLines is empty this function does nothing.
    :raises: SyntaxError if err in savedLines
    """
    if savedLines.strip() != "":
        try:
            saved_code_AST = ast.parse(savedLines)
        except SyntaxError:
            _, exc_obj, exc_tb = exc_info()
            raise UserError(exc_obj, exc_tb)

        imports = get_imports(saved_code_AST, savedLines)
        codeToExec = imports + "\n" + codeToExec

        # to make sure line # in errors is right we need to pad codeToExec with newlines
        numLinesToAdd = len(savedLines.split("\n")) - len(imports.split("\n"))
        for i in range(numLinesToAdd):
            codeToExec = "\n" + codeToExec

    return codeToExec
