import re
import datetime
import decimal
from arepl_jsonpickle.handlers import BaseHandler
from types import CodeType, FrameType, GeneratorType

NOT_SERIALIZABLE_MESSAGE = "not serializable by arepl"


class BaseCustomHandler(BaseHandler):
    """wrapper around BaseHandler for convenient unit testing"""

    def restore(self, obj):
        """just for unit testing"""
        return obj


class DatetimeHandler(BaseCustomHandler):
    ### better represention of datetime, see https://github.com/jsonpickle/jsonpickle/issues/109 ###
    def flatten(self, obj, data):
        x = {"date/time": str(obj)}
        return x


class DecimalHandler(BaseCustomHandler):
    def flatten(self, obj, data):
        x = float(obj)
        return x


class RegexMatchHandler(BaseCustomHandler):
    ### better represention of datetime, see https://github.com/jsonpickle/jsonpickle/issues/109 ###
    def flatten(self, obj, data):
        return {
            "py/object": "_sre.SRE_Match",
            "match": obj.group(0),
            "groups": obj.groups(),
            "span": obj.span(),
        }


class FrameHandler(BaseCustomHandler):
    ### better represention of frame, see https://github.com/Almenon/AREPL-backend/issues/26 ###
    def flatten(self, obj, data):
        if obj is None:
            return None
        return {
            "py/object": "types.FrameType",
            "f_back": self.flatten(obj.f_back, data),
            "f_builtins": NOT_SERIALIZABLE_MESSAGE,
            "f_code": CodeHandler(None).flatten(obj.f_code, data),
            "f_globals": NOT_SERIALIZABLE_MESSAGE,
            "f_lasti": obj.f_lasti,
            "f_lineno": obj.f_lineno,
            "f_locals": NOT_SERIALIZABLE_MESSAGE,
        }


class CodeHandler(BaseCustomHandler):
    ### better represention of frame, see https://github.com/Almenon/AREPL-backend/issues/26 ###
    def flatten(self, obj, data):
        return {
            "co_argcount": obj.co_argcount,
            "co_code": NOT_SERIALIZABLE_MESSAGE,
            "co_cellvars": obj.co_cellvars,
            "co_consts": NOT_SERIALIZABLE_MESSAGE,
            "co_filename": obj.co_filename,
            "co_firstlineno": obj.co_firstlineno,
            "co_flags": obj.co_flags,
            "co_lnotab": NOT_SERIALIZABLE_MESSAGE,
            "co_freevars": NOT_SERIALIZABLE_MESSAGE,
            "co_kwonlyargcount": obj.co_kwonlyargcount,
            "co_name": obj.co_name,
            "co_names": obj.co_names,
            "co_nlocals": NOT_SERIALIZABLE_MESSAGE,
            "co_stacksize": obj.co_stacksize,
            "co_varnames": obj.co_varnames,
        }


class GeneratorHandler(BaseCustomHandler):
    ### to prevent freeze-up when picking infinite generators, see https://github.com/Almenon/AREPL-backend/issues/96 ###
    def flatten(self, obj, data):
        return {
            "py/object": "builtins.generator",
        }


handlers = [
    {"type": datetime.date, "handler": DatetimeHandler},
    {"type": datetime.time, "handler": DatetimeHandler},
    {"type": datetime.datetime, "handler": DatetimeHandler},
    {"type": type(re.search("", "")), "handler": RegexMatchHandler},
    {"type": FrameType, "handler": FrameHandler},
    {"type": CodeType, "handler": CodeHandler},
    {"type": decimal.Decimal, "handler": DecimalHandler},
    {"type": GeneratorType, "handler": GeneratorHandler},
]
