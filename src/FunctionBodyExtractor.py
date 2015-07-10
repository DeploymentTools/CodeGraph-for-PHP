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

    # flags
    SQ = False  # is in single quote
    DQ = False  # is in double quote
    SLC = False # is in single line comment
    MLC = False # is in multi line comment

    cChar = ""
    pChar = ""

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

    def analyse_flags_quotes(self, expect, change_flag, override_flag):
        if (self.cChar == expect) and (self.pChar != '\\') and not override_flag:
            return not change_flag
        return change_flag

    def analyse_flags(self):
        current_phrase_content = self.phrase_content

        self.cChar = self.get_char(current_phrase_content, -1)
        self.pChar = self.get_char(current_phrase_content, -2)

        # print('---->' + current_phrase_content + '<----')

        if not self.SLC and not self.MLC:
            self.DQ = self.analyse_flags_quotes('"', self.DQ, self.SQ)
            self.SQ = self.analyse_flags_quotes("'", self.SQ, self.DQ)

        if not self.SQ and not self.DQ:
            if not self.MLC and (self.cChar == "/") and (self.pChar == '/') and not self.SLC:
                self.SLC = True
                # store current phrase, to resume after exiting from line comment. Strip the single line comment "//" chars
                self.phrase_transient_content = self.phrase_content[0:-2]
                # wipe current phrase, will be restored after phrase end
                self.phrase_content = ''
                # print('begin single comment')

            if (self.cChar == "*") and (self.pChar == '/') and (not self.MLC) and (not self.SLC):
                self.MLC = True
                # self.phrase_transient_content = self.phrase_content
                # print('begin multiline')

            if (self.cChar == "/") and (self.pChar == '*') and (self.MLC is True):
                self.MLC = False
                # self.phrase_transient_content = self.phrase_content
                self.phrase_content = ''
                # print('end multiline')

            if ((self.cChar == os.linesep) or (self.cChar == "\n") or (self.cChar == "\r\n")) and self.SLC:
                self.SLC = False
                # print('end single comment')

                # if not self.in_multi_line_comment:
                self.phrase_content = self.phrase_transient_content
                # print('reset phrase content')

        if (self.cChar == ';') and not self.SLC and not self.MLC and not self.SQ and not self.DQ:
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
    
        # elif (self.current_phrase['action'] == 'variable_prepare') and (self.current_char == '='):
        #     self.current_phrase['action'] = 'variable_set'
        #     self.think_about('waiting_for_variable_set')
        #     self.self.current_char.entities.append()


        # if (self.current_char == '"') or (self.current_char == "'"):
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