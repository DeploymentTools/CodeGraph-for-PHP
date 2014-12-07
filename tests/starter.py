import logging
import unittest

import sys
sys.path.append('src')
from FunctionBodyExtractor import FunctionBodyExtractor

# TODO  results aren't returned in the same order all the time. fix this in extract()
logging.basicConfig(level=logging.DEBUG)

class TestBA(unittest.TestCase):
    fbe = False

    def setUp(self):
        self.fbe = FunctionBodyExtractor()

        self.fbe.body = """
        $this->run();
        $this->counter++;

        $this->db = Registry::getInstance('DB');
        $this->db[0] = null;
"""

    def test_arrays_extracted(self):
        response = self.fbe.extract()
        response['arrays'].sort() # temp

        self.assertEqual(response['arrays'], ['$this->db'])

    def test_generic_extracted(self):
        response = self.fbe.extract()
        response['generic'].sort() # temp
        
        self.assertEqual(response['generic'], ['$this->counter', '$this->db'])

    def test_methods_extracted(self):
        response = self.fbe.extract()
        response['methods'].sort() # temp
        
        self.assertEqual(response['methods'], ['$this->run', 'Registry::getInstance'])

if __name__ == '__main__':
    unittest.main()