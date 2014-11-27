# The MIT License (MIT)

# Copyright (c) 2014 Bogdan Anton

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re

class FunctionBodyExtractor():
    signature = ""
    body = ""

    def extract(self):
        # WORD_reservedPHP = ['array', 'declare', 'die', 'class', 'echo', 'elseif', 'empty', 'eval', 'exit', 'for', 'foreach', 'global', 'if', 'include', 'include_once', 'isset', 'list', 'print', 'require', 'require_once', 'return', 'switch', 'unset', 'while', 'catch', 'or', 'and', 'xor']

        # TODO improve signature detection by checking if the variable was passed by reference. (Use this to check if the method body changes the variable passed by reference)
        # print(self.signature)
        textBody = self.body

        re.sub(r'\breturn\b', '', textBody)
        textBody = textBody.replace(" as ", "|as|").replace(" ", "").replace("\t", "")
        response = {}

        all_variables = re.findall(r'([a-zA-Z0-9_\:\-\>\$\(\)]+)\(', textBody)
        methods = []
        for variable in all_variables:
            if (('->' in variable) or ('::' in variable)):
                methods.append(variable)
            pass
        response['methods'] = list(set(methods))

        all_variables = re.findall(r'([a-zA-Z0-9_\:\-\>]+)\[', textBody)
        arrays = []
        for variable in all_variables:
            if (('->' in variable) or ('::' in variable)):
                arrays.append('$' + variable)
            pass
        response['arrays'] = list(set(arrays))

        all_variables = re.findall(r'\$([a-zA-Z0-9_\:\-\>]+)', textBody)
        class_attributes = []
        for variable in all_variables:
            if (('->' in variable) or ('::' in variable)):
                try:
                    response['methods'].index('$' + variable)
                    pass
                except ValueError:
                    class_attributes.append('$' + variable)
                    pass
            pass

        response['generic'] = list(set(class_attributes))

        return response