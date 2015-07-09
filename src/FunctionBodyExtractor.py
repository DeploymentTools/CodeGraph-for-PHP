# The MIT License (MIT)
#
# Copyright (c) 2014 Bogdan Anton
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
import os

class FunctionBodyExtractor():
    signature = ""
    body = ""

    phrase_transient_content = ""
    phrase_content = ""
    phrases_list = []
    current_phrase = {}

    # def get_last_thought(self):
    #     nr_thoughts = self.get_nr_thoughts();

    #     if nr_thoughts == 0:
    #         return None

    #     return self.current_phrase['thinking_about'][nr_thoughts - 1]

    # def get_nr_thoughts(self):
    #     return len(self.current_phrase['thinking_about'])

    # def think_about(self, message):
    #     thought = message

    #     existing_thoughts_nr = self.get_nr_thoughts()

    #     if ((existing_thoughts_nr > 0) and (self.get_last_thought() != thought)) or (existing_thoughts_nr == 0):
    #         self.current_phrase['thinking_about'].append(thought)

    in_single_quotes = False
    in_double_quotes = False
    in_single_comment = False
    in_multi_line_comment = False
    is_end_of_phrase = False

    def get_char(self, content, offset_end):
        char = None

        if content and isinstance(content, str) and len(content) > 0:
            size_content = len(content)
            if offset_end < 0:
                if offset_end + size_content >= 0:
                    char = content[size_content + offset_end]
                
            elif offset_end < size_content:
                char = content[offset_end]

        return char

    def analyse_flags(self):
        current_phrase_content = self.phrase_content

        current_char = self.get_char(current_phrase_content, -1)
        previous_char = self.get_char(current_phrase_content, -2)

        # print('---->' + current_phrase_content + '<----')

        if not self.in_single_comment and not self.in_multi_line_comment:
            if (current_char == "'") and (previous_char != '\\') and (self.in_double_quotes is False):
                self.in_single_quotes = not self.in_single_quotes

            if (current_char == '"') and (previous_char != '\\') and (self.in_single_quotes is False):
                self.in_double_quotes = not self.in_double_quotes

        if not self.in_single_quotes and not self.in_double_quotes:
            if not self.in_multi_line_comment and (current_char == "/") and (previous_char == '/') and not self.in_single_comment:
                self.in_single_comment = True
                # store current phrase, to resume after exiting from line comment. Strip the single line comment "//" chars
                self.phrase_transient_content = self.phrase_content[0:-2]
                # wipe current phrase, will be restored after phrase end
                self.phrase_content = ''
                # print('begin single comment')

            if (current_char == "*") and (previous_char == '/') and (not self.in_multi_line_comment) and (not self.in_single_comment):
                self.in_multi_line_comment = True
                # self.phrase_transient_content = self.phrase_content
                # print('begin multiline')

            if (current_char == "/") and (previous_char == '*') and (self.in_multi_line_comment is True):
                self.in_multi_line_comment = False
                # self.phrase_transient_content = self.phrase_content
                self.phrase_content = ''
                # print('end multiline')

            if ((current_char == os.linesep) or (current_char == "\n") or (current_char == "\r\n")) and self.in_single_comment:
                self.in_single_comment = False
                # print('end single comment')

                # if not self.in_multi_line_comment:
                self.phrase_content = self.phrase_transient_content
                # print('reset phrase content')

        if (current_char == ';') and not self.in_single_comment and not self.in_multi_line_comment and not self.in_single_quotes and not self.in_double_quotes:
            self.is_end_of_phrase = True

    def analise_phrase(self):
        self.analyse_flags()

        if self.is_end_of_phrase:
            self.phrases_list.append(self.phrase_content)
            self.phrase_content = ''
            self.is_end_of_phrase = False

        # startsWithVariable = re.findall(r'^(\$[\w\d]+)$', current_phrase_content)
        # startsWithDollar = re.findall(r'^(\$)$', current_phrase_content)

        # if (startsWithDollar):
        #     self.think_about('expecting_closure_or_variable')

        # elif (startsWithVariable):
        #     self.current_phrase['action'] = 'variable_prepare' # probably will set
        #     self.current_phrase['subject'] = startsWithVariable
        #     self.think_about('building_variable')
    
        # elif (self.current_phrase['action'] == 'variable_prepare') and (current_char == '='):
        #     self.current_phrase['action'] = 'variable_set'
        #     self.think_about('waiting_for_variable_set')
        #     self.current_char.entities.append()


        # if (current_char == '"') or (current_char == "'"):
        #     if (self.get_last_thought() == 'listening_for_string'):
        #         self.think_about('stop_listening_for_string')

        # print([self.phrase_content, self.current_phrase])

    def appendChar(self, x):
        if ((self.phrase_content == "") and (x.strip() == "")) == False:
            self.phrase_content += x
            self.analise_phrase()

    def reset(self):
        self.current_phrase['type'] = False
        self.current_phrase['action'] = False
        self.current_phrase['subject'] = False
        self.current_phrase['thinking_about'] = []
        self.current_phrase['entities'] = []

    # will split the method into "phrases"
    def phrases(self):
        self.reset()

        for x in self.body:
            # if x.strip() != "":
            #     print(x)
            #
            self.appendChar(x)
            pass

    def extract(self):
        # WORD_reservedPHP = ['array', 'declare', 'die', 'class', 'echo', 'elseif', 'empty', 'eval', 'exit', 'for', 'foreach', 'global', 'if', 'include', 'include_once', 'isset', 'list', 'print', 'require', 'require_once', 'return', 'switch', 'unset', 'while', 'catch', 'or', 'and', 'xor']

        # TODO improve signature detection by checking if the variable was passed by reference. (Use this to check if the method body changes the variable passed by reference)
        # print(self.signature)
        textBody = self.body

        re.sub(r'\breturn\b', '', textBody)
        textBody = textBody.replace(" as ", "|as|").replace("\t", "")
        response = {}

        all_variables = re.findall(r'([a-zA-Z0-9\s_\:\-\>\$\(\)]+)\(', textBody)
        methods = []
        for variable in all_variables:
            if (('->' in variable) or ('::' in variable)):
                methods.append(variable.strip())
            pass
        response['methods'] = list(set(methods))

        all_variables = re.findall(r'([a-zA-Z0-9\s_\:\-\>]+)\[', textBody)
        arrays = []
        for variable in all_variables:
            if (('->' in variable) or ('::' in variable)):
                arrays.append('$' + variable.strip())
            pass
        response['arrays'] = list(set(arrays))

        all_variables = re.findall(r'\$([a-zA-Z0-9\s_\:\-\>]+)', textBody)
        class_attributes = []
        for variable in all_variables:
            if (('->' in variable) or ('::' in variable)):
                try:
                    response['methods'].index('$' + variable.strip())
                    pass
                except ValueError:
                    class_attributes.append('$' + variable.strip())
                    pass
            pass

        response['generic'] = list(set(class_attributes))

        response['arrays'].sort()
        response['methods'].sort()
        response['generic'].sort()

        return response