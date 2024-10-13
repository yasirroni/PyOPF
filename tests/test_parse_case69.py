import unittest
import opf
from pathlib import Path
import pyomo.environ as pyo

class ParseCase69Test(unittest.TestCase):
    def test_parse(self):
        matpower_fn = Path("./data/case69.m")
        network = opf.parse_file(matpower_fn)

if __name__ == '__main__':
    unittest.main()