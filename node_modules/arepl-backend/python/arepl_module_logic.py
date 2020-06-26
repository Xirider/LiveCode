from sys import version
from sys import builtin_module_names
from sys import modules
from pkgutil import iter_modules
from arepl_stdlib_list import stdlib_list
from typing import List,Set

def get_non_user_modules() -> Set[str]:
    """returns a set of all modules not written by the user (aka all builtin and pip modules)
    
    Returns:
        set -- set of module names
    """
    # p[1] is name
    pip_modules = [p[1] for p in iter_modules()]  # pylint: disable=E1133

    more_builtin_modules = stdlib_list(version[:3], fallback=True)
    # more_builtin_modules contains modules in libs folder, among many others

    even_more_builtin_modules = [k for k in modules]
    # how many damn modules are there???

    return set(
        pip_modules + list(builtin_module_names) + more_builtin_modules + even_more_builtin_modules
    )
