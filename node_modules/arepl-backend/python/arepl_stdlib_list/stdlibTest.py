import unittest
from . import stdlib_list


class TestStdlibList(unittest.TestCase):
    def test_stdlib_list_returns_results(self):
        returnInfo = stdlib_list()
        assert len(returnInfo) != 0


if __name__ == '__main__':
    unittest.main()
