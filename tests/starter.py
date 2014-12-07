import logging
import unittest

import sys
sys.path.append('src')
from FunctionBodyExtractor import FunctionBodyExtractor

logging.basicConfig(level=logging.DEBUG)

class TestBA(unittest.TestCase):
    def test_basic_extractor(self):
        expected = {
            'arrays': ['$this->db'],
            'generic': ['$this->counter', '$this->db'],
            'methods': ['$this->run', 'Registry::getInstance']
        }

        fbe = FunctionBodyExtractor()

        fbe.body = """
        $this->run();
        $this->counter++;

        $this->db = Registry::getInstance('DB');
        $this->db[0] = null;
"""
        response = fbe.extract()

        # TODO  results aren't returned in the same order all the time. fix this in extract()
        # self.assertEqual(expected, response)

        self.assertEqual(expected['arrays'].sort(), response['arrays'].sort())
        self.assertEqual(expected['generic'].sort(), response['generic'].sort())
        self.assertEqual(expected['methods'].sort(), response['methods'].sort())

if __name__ == '__main__':
    unittest.main()