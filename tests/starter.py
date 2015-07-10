import logging
import unittest

logging.basicConfig(level=logging.DEBUG)

import sys
sys.path.append('src')

from FunctionBodyExtractor import FunctionBodyExtractor

class TestGetChar(unittest.TestCase):

    def test_when_last_char_is_string_then_return_the_char(self):
        fbe = FunctionBodyExtractor()

        response = fbe.get_char('content123', -1)
        self.assertEqual('3', response)

    def test_when_last_char_is_space_then_return_the_empty_space_char(self):
        fbe = FunctionBodyExtractor()

        response = fbe.get_char('content123 ', -1)
        self.assertEqual(' ', response)

    def test_when_input_string_is_empty_then_return_None(self):
        fbe = FunctionBodyExtractor()

        response = fbe.get_char('', -1)
        self.assertEqual(None, response)

    def test_when_input_is_None_then_return_None(self):
        fbe = FunctionBodyExtractor()

        response = fbe.get_char(None, -1)
        self.assertEqual(None, response)

    def test_when_input_is_string_and_offset_is_zero_then_get_first_char(self):
        fbe = FunctionBodyExtractor()

        response = fbe.get_char('abcdef', 0)
        self.assertEqual('a', response)

    def test_when_input_is_string_and_offset_is_positive_then_get_char(self):
        fbe = FunctionBodyExtractor()

        response = fbe.get_char('ABCDEF', 2)
        self.assertEqual('C', response)

    def test_when_input_is_string_and_offset_is_greater_than_string_length_then_return_None(self):
        fbe = FunctionBodyExtractor()

        response = fbe.get_char('ABCDEF', 10)
        self.assertEqual(None, response)


class TestAnaliseFlags(unittest.TestCase):
    fbe = None

    def setUp(self):
        self.fbe = FunctionBodyExtractor()

    def assert_flags(self, expect_in_single_quotes, expect_in_double_quotes, expect_in_single_comment, expect_in_multi_line_comment):
        self.assertEqual(expect_in_single_quotes, self.fbe.SQ)
        self.assertEqual(expect_in_double_quotes, self.fbe.DQ)
        self.assertEqual(expect_in_single_comment, self.fbe.SLC)
        self.assertEqual(expect_in_multi_line_comment, self.fbe.MLC)

    def set_content_and_run_assert(self, content, SQ, DQ, SLC, MLC):
        self.fbe.phrase_content = content
        self.fbe.analyse_flags()
        self.assert_flags(SQ, DQ, SLC, MLC)

    def test_when_string_opened_single_quotes_then_change_single_quote_to_true_if_all_other_flags_are_false(self):
        self.set_content_and_run_assert("$a = '", True, False, False, False)

    def test_when_string_opened_double_quotes_then_change_double_quote_to_true_if_all_other_flags_are_false(self):
        self.set_content_and_run_assert('$a = "', False, True, False, False)

    def test_when_string_opened_single_quotes_and_is_in_single_line_comment_then_dont_change_single_quote_flag(self):
        self.fbe.SLC = True
        self.set_content_and_run_assert('$a = "', False, False, True, False)

    def test_when_string_opened_single_quotes_and_is_in_multiline_comment_then_dont_change_single_quote_flag(self):
        self.fbe.MLC = True
        self.set_content_and_run_assert('$a = "', False, False, False, True)

    def test_when_not_in_quotes_and_is_start_of_single_line_comment_then_change_single_line_flag(self):
        self.set_content_and_run_assert('$a = 1; //', False, False, True, False)

    def test_when_in_quotes_and_is_start_of_single_line_comment_then_dont_change_single_line_flag(self):
        # single quotes
        self.fbe.SQ = True

        self.fbe.phrase_content = '$a = 1; //'
        self.fbe.analyse_flags()

        self.fbe.SQ = False # reset
        self.assert_flags(False, False, False, False)

        # double quotes
        self.fbe.DQ = True

        self.fbe.phrase_content = '$a = 1; //'
        self.fbe.analyse_flags()

        self.fbe.DQ = False # reset
        self.assert_flags(False, False, False, False)

    def test_when_not_in_quotes_and_is_start_of_multi_line_comment_then_change_multi_line_flag(self):
        self.set_content_and_run_assert('$a = 1; /*', False, False, False, True)

    def test_when_in_quotes_and_is_start_of_multi_line_comment_then_dont_change_multi_line_flag(self):
        # single quotes
        self.fbe.DQ = True
        self.set_content_and_run_assert('$a = 1; /*', False, True, False, False)
        self.fbe.DQ = False

        # double quotes
        self.fbe.SQ = True
        self.set_content_and_run_assert('$a = 1; /*', True, False, False, False)

    def test_when_in_single_line_comment_and_is_multi_line_comment_then_change_multi_line_flag(self):
        self.set_content_and_run_assert("$a = 1; //", False, False, True, False)

        self.fbe.phrase_content = """$a = 1; //
"""
        self.fbe.analyse_flags()
        self.assert_flags(False, False, False, False)

        self.fbe.phrase_content = """$a = 1; //
/"""
        self.fbe.analyse_flags()
        self.assert_flags(False, False, False, False)

        self.fbe.phrase_content = """$a = 1; //
/*"""
        self.fbe.analyse_flags()
        self.assert_flags(False, False, False, True)

        self.fbe.phrase_content = """$a = 1; //
/*a"""
        self.fbe.analyse_flags()
        self.assert_flags(False, False, False, True)

        self.fbe.phrase_content = """$a = 1; //
/*a*"""
        self.fbe.analyse_flags()
        self.assert_flags(False, False, False, True)

        self.fbe.phrase_content = """$a = 1; //
/*a*/"""
        self.fbe.analyse_flags()
        self.assert_flags(False, False, False, False)

    def test_when_latest_char_is_end_of_line_then_reset_single_comment_flag(self):
        self.fbe.SLC = True
        self.fbe.phrase_content = """$a = 1;
"""
        self.fbe.analyse_flags()
        self.assert_flags(False, False, False, False)

        self.fbe.SLC = True
        self.fbe.phrase_content = """$a = 1;\n"""
        self.fbe.analyse_flags()
        self.assert_flags(False, False, False, False)


class TestPhrases(unittest.TestCase):
    fbe = None

    def setUp(self):
        self.fbe = FunctionBodyExtractor()

    def test_get_simple_phrases(self):
        self.fbe.body = """
            $a = 'abc';
            // $b = '123';

            /*
            $c = 'DEF';
            */

            $d = new \stdClass;
        """

        self.fbe.phrases()
        self.assertEqual(["$a = 'abc';", "$d = new \stdClass;"], self.fbe.phrases_list)

    @unittest.skip("extract blocks as phrases/stories")
    def test_get_if_statement_phrase(self):

        self.fbe.body = """
            static $statement = false;

            if (isset($content0)) {
                $a = 2;
                die(0);
            }

            if (isset($content1)) { // explain
                // if something then exit
                exit();
            }

            if (isset($content2) /* && $isDebug */) {
                die(2);
            }

            return '123';
"""
        self.fbe.phrases()

        expected = []
        expected.append("static $statement = false;")

        self.assertEqual(expected, self.fbe.phrases_list)


#        self.fbe.body = """
#        $this->run();
#        $this->counter++;
#
#        $this->db = Registry::getInstance('DB');
#        $this->db[0] = null;
#"""
#
#     def test_arrays_extracted(self):
#         response = self.fbe.extract()
#         self.assertEqual(response['arrays'], ['$this->db'])
#
#     def test_generic_extracted(self):
#         response = self.fbe.extract()
#         self.assertEqual(response['generic'], ['$this->counter', '$this->db'])
#
#     def test_get_static_class_method(self):
#         self.fbe = FunctionBodyExtractor()
#
#         self.fbe.body = """
#         $this->db = Registry::getInstance('DB');
# """
#         response = self.fbe.extract()
#         self.assertEqual(response['methods'], ['Registry::getInstance'])
#
#     def test_get_static_object_method(self):
#         self.fbe = FunctionBodyExtractor()
#
#         self.fbe.body = """
#         $s = new \Core;
#         $this->db = $s::getInstance('DB');
# """
#         response = self.fbe.extract()
#         self.assertEqual(response['methods'], ['$s::getInstance'])
#
#     # note: check
#     def test_get_static_container_method(self):
#         self.fbe = FunctionBodyExtractor()
#
#         self.fbe.body = """
#         $s = new \Core;
#         $this->db = $s[$databaseEngine]::getInstance('DB');
# """
#         response = self.fbe.extract()
#         self.assertEqual(response['methods'], ['$s[$databaseEngine]::getInstance'])

if __name__ == '__main__':
    unittest.main()