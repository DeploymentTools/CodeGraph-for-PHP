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

import sublime, sublime_plugin
import time
import re, os, io
from time import sleep
import json

class JumpToMethodCommand(sublime_plugin.TextCommand):
    use_manual_path = False
    project_path    = "/projects/PHP-CodeGraph/demo/"
    log_path        = "/projects/PHP-CodeGraph/demo/"

    def prepareFolders(self):
        if (self.use_manual_path):
            project_data = sublime.active_window().project_data()
            project_folder = project_data['folders']
            project_folder = [{'path': self.project_path, 'follow_symlinks': True}]
        else:
            project_data = sublime.active_window().project_data()
            project_folder = project_data['folders']

        return project_folder

    def run(self, edit):
        project_folder = self.prepareFolders()

        worker = ClassExtractor()
        worker.setConfig('basepath', self.project_path)
        worker.setConfig('logpath', self.log_path)
        # worker.setConfig('debug', True)
        worker.processMain()

        for (item) in project_folder:
            worker.traverseFolders(item['path'])

        worker.processMain()


class ClassExtractor():
    allFilesList      = []
    allowedExtensions = ['php']
    excludeFolders    = ['tests', '.git']
    outlineIndex      = []
    limitFiles        = 0
    cursorFiles       = 0

    listVariableKeywords  = ['public', 'private', 'protected', 'var', 'static']
    listConstantsKeywords = ['const']
    listFunctionAccess    = ['public', 'private', 'protected']
    listFunctionStatic    = ['static']

    config = {
        'basepath': '',
        'logpath': '/var/log/',
        'debug': False,
        'flag.processMethodBody': True,
        'flag.processMethodSignature': True,
        'flag.processClassConstants': True,
        'flag.processClassAttributes': True,
        'flag.processJSONOutput': True
    }

    logData = []

    # transient flags
    previousChar                  = ""
    previous2Char                 = ""
    previousWord                  = ""
    previous2Word                 = ""
    previous3Word                 = ""
    previous4Word                 = ""
    previous5Word                 = ""
    currentClass                  = ""
    currentIsComment              = False
    currentIsMethod               = False
    currentIsStringInSingleQuotes = False
    currentIsStringInDoubleQuotes = False
    currentIsPHP                  = False
    currentLineCursor             = -1;
    currentClassName              = ""
    currentClassAccess            = ""
    currentClassExtends           = []
    currentClassImplements        = []
    currentFunctionName           = ""
    currentFunctionAccess         = ""
    currentFunctionStatic         = False
    currentFunctionBody           = ""
    currentBracketLevel           = 0
    currentNamespace              = ""
    previousNamespace             = ""
    listenForFunctionSignature    = False
    currentFunctionSignature      = ""
    listenForClassAttribute       = False
    currentClassAttribute         = ""
    ignoreUntilLineEnd            = False
    currentClassConstant          = ""
    listenForClassConstant        = False
    latestDocblock                = ""
    listenForPHPCode              = False
    isInsidePHPShortBlock         = False
    cursorCharacter               = ""

    def getConfig(self, key):
        return self.config[key]

    def setConfig(self, key, value):
        self.config[key] = value
        return True

    def processMain(self):
        self.traverseFolders(self.getConfig('basepath'))

        for filepath in self.allFilesList:
            if (self.limitFiles == 0 or (self.limitFiles > 0 and self.limitFiles >= self.cursorFiles)):
                try:
                    if (self.getConfig('debug')):
                        print(filepath)

                    self.processFile(filepath)
                except UnicodeDecodeError:
                    pass
            self.cursorFiles = self.cursorFiles + 1

        self.writeJSONOutput()

    def isAClassVariableKeyword(self):
        try:
            if (self.listVariableKeywords.index(self.previousWord.lower()) >= 0):
                return True
        except ValueError:
            pass
        return False

    def isAClassConstantKeyword(self):
        try:
            if (self.listConstantsKeywords.index(self.previousWord.lower()) >= 0):
                return True
        except ValueError:
            pass
        return False

    def extractClassAttribute(self, char, filepath):
        if (self.getConfig('flag.processClassAttributes') == False):
            return False

        isAClassVariableKeyword = self.isAClassVariableKeyword()

        if ((char == '$') and (isAClassVariableKeyword)):
            self.listenForClassAttribute = True

        if ((self.currentClassAttribute != '') & ((char == '=') | (char == ';') | (char == ' ') | (char == ',') | (char == '\t') | (char == '\n'))):
            self.listenForClassAttribute = False
            
            if (self.currentClassAttribute != ""):
                attributeName = self.currentClassAttribute
                attributeAccess = "_public_"
                attributeStatic = False

                try:
                    if (self.listFunctionAccess.index(self.previous2Word.lower()) >= 0):
                        attributeAccess = self.previous2Word.lower()
                except ValueError:
                    pass
                    
                try:
                    if (self.listFunctionAccess.index(self.previous3Word.lower()) >= 0):
                        attributeAccess = self.previous3Word.lower()
                except ValueError:
                    pass
                    
                try:
                    if ((self.previous3Word.lower() == 'static') | (self.previous2Word.lower() == 'static')):
                        attributeStatic = True
                except ValueError:
                    pass

                docblock = self.latestDocblock.replace("\n\t", "\n")

                entry = {'item': 'class_attribute', 'name': attributeName, 'access': attributeAccess, 'static': attributeStatic, 'file': filepath, 'line': str(self.currentLineCursor), 'namespace': self.getNamespace(), 'class': self.currentClassName, 'docblock': docblock}
                self.logData.append(entry)
                self.latestDocblock = ""

            self.currentClassAttribute = ""

        if (self.listenForClassAttribute):
            self.currentClassAttribute += char

    def extractClassConstant(self, char, filepath):
        if (self.getConfig('flag.processClassConstants') == False):
            return False

        isAClassConstantKeyword = self.isAClassConstantKeyword()

        if ((char != ' ') and (isAClassConstantKeyword)):
            self.listenForClassConstant = True

        if ((self.currentClassConstant != '') & ((char == '=') | (char == ';') | (char == ' ') | (char == '\t') | (char == '\n'))):
            self.listenForClassConstant = False
            
            if (self.currentClassConstant != ""):
                docblock = self.latestDocblock.replace("\n\t", "\n")
                self.logData.append({'item': 'class_constant', 'name': self.currentClassConstant, 'file': filepath, 'line': str(self.currentLineCursor), 'namespace': self.getNamespace(), 'class': self.currentClassName, 'docblock': docblock})
                self.latestDocblock = ""

            self.currentClassConstant = ""

        if (self.listenForClassConstant):
            self.currentClassConstant += char

    def processFile(self, filepath):
        self.resetFileStatistics()

        file = open(filepath, 'r')
        for line in file:
            self.currentLineCursor += 1
            for char in line:
                self.registerCurrentChar(char)

                if (self.currentIsComment == True):
                    self.latestDocblock += char

                if (char != " "):
                    if (self.ignoreUntilLineEnd):
                        if (char != "\n"):
                            continue
                        else:
                            self.ignoreUntilLineEnd = False
                    
                    if (self.currentIsStringInDoubleQuotes == False & self.currentIsStringInSingleQuotes == False):
                        if ((char == '?') and (self.previousChar == "<")):
                            if (self.isInsidePHPShortBlock == False):
                                self.listenForPHPCode = True
                            else:
                                self.isInsidePHPShortBlock = False

                        if ((char == '>') and (self.previousChar == '?')):
                            if (self.isInsidePHPShortBlock == False):
                                self.listenForPHPCode = False
                            else:
                                self.isInsidePHPShortBlock == False

                        if ((self.previous2Char == '<') and (self.previousChar == '?') and (char == '=')):
                            self.isInsidePHPShortBlock

                    if (char == '"'):
                        if (self.currentIsComment == False):
                            self.currentIsStringInDoubleQuotes = not self.currentIsStringInDoubleQuotes
                        
                    if (char == "'"):
                        if (self.currentIsComment == False):
                            self.currentIsStringInSingleQuotes = not self.currentIsStringInSingleQuotes

                    # should we skip the line if not in multi comment?
                    if (char == '/' and self.previousChar == "/"):
                        if (self.currentIsStringInDoubleQuotes == False & self.currentIsStringInSingleQuotes == False):
                            self.previousChar = ""
                            
                            if (self.currentIsComment == False):
                                self.ignoreUntilLineEnd = True

                            continue

                    if ((char == '*') and (self.previousChar == "/")):
                        if (self.currentIsStringInDoubleQuotes == False & self.currentIsStringInSingleQuotes == False):
                            self.currentIsComment = True
                            self.latestDocblock = "/*"

                    if ((char == 't') and (self.previousChar == "\\")):
                        self.previousChar = " "

                    if ((char == '\t') or (char == '\n') or (char == '\r\n')):
                        self.previousChar = " "
                        self.collectFunctionBody()
                        continue

                    if ((char == '/') and (self.previousChar == "*")):
                        if (self.currentIsStringInDoubleQuotes == False & self.currentIsStringInSingleQuotes == False):
                            self.currentIsComment = False

                    # don't sniff beyond this point when not inside a PHP block
                    if (self.listenForPHPCode == False):
                        self.previous2Char = self.previousChar
                        self.previousChar = char
                        continue

                    self.collectFunctionBody()

                    # CLASS ATTRIBUTES
                    if (self.currentIsComment == False & self.currentIsStringInDoubleQuotes == False & self.currentIsStringInSingleQuotes == False):
                        if ((self.currentBracketLevel == 1) and (self.currentClassName != "")):
                            self.extractClassAttribute(char, filepath)
                            self.extractClassConstant(char, filepath)

                    # FUNCTIONS
                    if ((char == "(") and self.currentIsComment == False & self.currentIsStringInDoubleQuotes == False & self.currentIsStringInSingleQuotes == False):
                        if ((self.previous2Word == 'function') or (self.previous4Word == 'function') or (self.previous3Word == 'function')):
                            self.listenForFunctionSignature = True
                            self.currentFunctionSignature = ""
                            # print('will be listening')

                    if ((char == "{") & (self.currentIsComment == False & self.currentIsStringInDoubleQuotes == False & self.currentIsStringInSingleQuotes == False)):
                        self.listenForFunctionSignature = False
                        # print('will stop listening ' + char)

                    if ((self.previousChar == " ") or (char == "{") or (char == "(")):
                        if (self.currentIsComment == False):
                            self.previous5Word = self.previous4Word
                            self.previous4Word = self.previous3Word
                            self.previous3Word = self.previous2Word
                            self.previous2Word = self.previousWord
                            self.previousWord = ""
                            # print([self.previous5Word, self.previous4Word, self.previous3Word, self.previous2Word])

                    if (self.listenForFunctionSignature == True):
                        self.currentFunctionSignature += char
                        # print('listened and catched ' + char)
                    
                    if ((self.currentIsComment == False & self.currentIsStringInDoubleQuotes == False & self.currentIsStringInSingleQuotes == False)):
                        if ((self.previous2Word == 'namespace') and (char == ';')):
                            self.currentNamespace = self.previousWord

                    if (self.currentIsComment == False):
                        self.previousWord += char

                    if ((self.previous4Word == 'class') and (self.currentIsComment == False)):
                        bracketLevel = self.currentBracketLevel
                        if ((self.previous2Word == '{') or (self.previousWord == '{')):
                            bracketLevel -= 1

                        if (bracketLevel == 0):
                            self.currentClassName = self.previous3Word
                        #print('possible class: ' + self.previous3Word + ' and function is ' + self.currentFunctionName + ' and bracket level is ' + str(bracketLevel))

                    if (self.currentIsStringInDoubleQuotes == False & self.currentIsStringInSingleQuotes == False):
                        if ((char == '(') and (self.currentIsComment == False)):
                            
                            if (self.previous3Word == 'function'):
                                self.currentFunctionName = self.previous2Word

                                if self.previous4Word in self.listFunctionAccess:
                                    self.currentFunctionAccess = self.previous4Word

                                if self.previous5Word in self.listFunctionAccess:
                                    self.currentFunctionAccess = self.previous5Word

                                self.currentFunctionStatic = ((self.previous4Word in self.listFunctionStatic) or (self.previous5Word in self.listFunctionStatic))

                                isStaticBool = False
                                isStatic = "->"
                                if (self.currentFunctionStatic):
                                    isStaticBool = True
                                    isStatic = "::"

                                # print([self.currentClassName, isStatic, self.currentFunctionAccess, self.currentFunctionName, 'line: ' + str(self.currentLineCursor), 'bracket level: ' + str(self.currentBracketLevel)])
                                # print([self.previous5Word, self.previous4Word, self.previous3Word, self.previous2Word])

                    if (self.currentIsStringInDoubleQuotes == False and self.currentIsStringInSingleQuotes == False and self.currentIsComment == False):
                        if (char == '{'):
                            self.currentBracketLevel += 1
                            if (self.currentBracketLevel == 1 and self.currentClassName == ""):
                                self.currentFunctionBody = "{"
                            if (self.currentBracketLevel == 2 and self.currentClassName != ""):
                                self.currentFunctionBody = "{"

                        if (char == '}'):
                            self.currentBracketLevel -= 1
                            if (self.currentBracketLevel <= 1):
                                # self.currentFunctionBody = ""

                                if (self.currentFunctionName != ''):
                                    functionSignature = self.processFunctionSignature(self.currentFunctionSignature)
                                    
                                    if (self.currentFunctionAccess == ""):
                                        self.currentFunctionAccess = "_public_"
                                    
                                    namespace = self.getNamespace()

                                    functionAccess = self.currentFunctionAccess
                                    className = self.currentClassName
                                    if (className == ""):
                                        isStaticBool = False
                                        isStatic = ""
                                        functionAccess = ""

                                    docblock = self.latestDocblock.replace("\n\t", "\n")

                                    logDataEntry              = {}
                                    logDataEntry['item']      = 'class_method'
                                    logDataEntry['name']      = self.currentFunctionName
                                    logDataEntry['file']      = filepath
                                    logDataEntry['line']      = str(self.currentLineCursor)
                                    logDataEntry['namespace'] = namespace
                                    logDataEntry['class']     = className
                                    logDataEntry['isStatic']  = isStaticBool
                                    logDataEntry['access']    = functionAccess
                                    logDataEntry['signature'] = functionSignature
                                    logDataEntry['docblock']  = docblock
                                    logDataEntry['body']      = self.getFunctionBody(functionSignature, self.currentFunctionBody)

                                    self.logData.append(logDataEntry)

                                    if ((logDataEntry['class']) and (self.getConfig('debug'))):
                                        print("")
                                        print("=====================================")
                                        if (isStaticBool):
                                            print(logDataEntry['class'] + "::" + logDataEntry['name'])
                                        else:
                                            print(logDataEntry['class'] + "->" + logDataEntry['name'])
    
                                        print(logDataEntry['body'])

                                # clean
                                self.currentFunctionName = ""
                                self.currentFunctionAccess = ""
                                self.currentFunctionStatic = False
                                self.currentFunctionBody = ""
                                self.latestDocblock = ""

                            if (self.currentBracketLevel == 0):
                                self.currentClassName = ""
                                if (self.currentNamespace != ""):
                                    self.previousNamespace = self.currentNamespace
                                    self.currentNamespace = ""

                else:
                    self.collectFunctionBody()

                    if (self.listenForFunctionSignature == True):
                        self.currentFunctionSignature += char

                self.previous2Char = self.previousChar
                self.previousChar = char

        file.close()
        pass

    def getFunctionBody(self, functionSignature, functionBody):
        functionBodyExtractor = FunctionBodyExtractor()
        functionBodyExtractor.signature = functionSignature
        functionBodyExtractor.body = functionBody

        return functionBodyExtractor.extract()

    def isWordMethodCall(self, word):
        if ("::" in word or "->" in word):
            return True
        else:
            return False

    def registerCurrentChar(self, cursorCharacter):
        self.cursorCharacter = cursorCharacter

    def collectFunctionBody(self):
        if (self.getConfig('flag.processMethodBody')):
            if (((self.currentBracketLevel > 1) and (self.currentClassName != "")) or ((self.currentBracketLevel > 0) and (self.currentClassName == ""))):
                self.currentFunctionBody += self.cursorCharacter

    def getNamespace(self):
        namespace = self.currentNamespace
        if ((self.currentNamespace == "") & (self.previousNamespace != "")):
            namespace = self.previousNamespace
        return namespace

    def processFunctionSignature(self, originalSignature):
        if (self.getConfig('flag.processMethodSignature') == False):
            return ""

        signature = originalSignature.strip()[1:-1].strip()

        if (signature == ""):
            signature = False
        else:
            variables             = []
            listenForVariable     = False
            listenForType         = True
            listenForDefaultValue = False
            variable              = ""
            variableType          = ""
            variableDefaultValue  = ""
            listenForDefault      = False
            defaultValue          = ""
            paranthesisLevel      = 0
            inSingleQuotes        = False
            inDoubleQuotes        = False

            signature = signature + "," # for splitting purpose

            for char in signature:
                if ((char == ',') and (inSingleQuotes == False) and (paranthesisLevel == 0) and (inDoubleQuotes == False)):
                    # prepare default type
                    description = ""

                    if (variable != ""):
                        if (variableType == ""):
                            variableType = ''
                            if (self.latestDocblock != ""):
                                # print(self.latestDocblock)
                                m = re.findall(r"\@param ([a-zA-Z0-9_\$\\ ]+) "+re.escape(str(variable))+" ([\'\"\-\\., a-zA-Z0-9_]+)", self.latestDocblock, re.DOTALL)
                                if (m):
                                    variableType = str(m[0])
                                    try:
                                        description = str(m[1])
                                    except IndexError:
                                        pass
                                else:
                                    defaultValue = defaultValue.strip()
                                    if (defaultValue != ""):
                                        if ((defaultValue[0] == '"') or (defaultValue[0] == "'")):
                                            variableType = 'string'

                    # append
                    signatureArgument = {}
                    
                    if (variableType.strip() != ""):
                        signatureArgument['t'] = variableType.strip()

                    if (defaultValue.strip() != ""):
                        signatureArgument['v'] = defaultValue.strip()

                    try:
                        if (description.strip() != ""):
                            signatureArgument['d'] = description
                    except AttributeError:
                        pass

                    signatureArgument['n'] = variable

                    if (signatureArgument != {}):
                        variables.append(signatureArgument)

                    # clean
                    listenForDefault = False
                    variableType     = ""
                    listenForType    = False
                    variable         = ""
                    defaultValue     = ""
                    variableType     = ""

                else:
                    if (char == '('):
                        paranthesisLevel += 1

                    if (char == ')'):
                        paranthesisLevel -= 1

                    if ((char == "'") and (self.previousChar != '\\')):
                        inSingleQuotes = not inSingleQuotes

                    if ((char == '"') and (self.previousChar != '\\')):
                        inDoubleQuotes = not inDoubleQuotes

                    if ((char != '$') and (variable == '') and (listenForType == True) and (listenForVariable == False)):
                        variableType += char

                    if (char == '$'):
                        listenForVariable = True
                        variable = ''

                    if ((listenForVariable == True) and (char != " ")):
                        variable += char

                    if (listenForDefault):
                        defaultValue += char

                    if (char == "="):
                        listenForDefault = True

                if ((char == " ") or (char == "=")):
                    listenForVariable = False

            signature = variables

        return signature

    def resetFileStatistics(self):
        self.currentClass                  = ""
        self.currentIsComment              = False
        self.currentIsMethod               = False
        self.currentIsStringInSingleQuotes = False
        self.currentIsStringInDoubleQuotes = False
        self.currentIsPHP                  = False
        self.previousChar                  = ""
        self.previous2Char                 = ""
        self.previousWord                  = ""
        self.previous2Word                 = ""
        self.previous3Word                 = ""
        self.previous4Word                 = ""
        self.previous5Word                 = ""
        self.currentLineCursor             = -1;
        self.currentClassName              = ""
        self.currentClassAccess            = ""
        self.currentClassExtends           = []
        self.currentClassImplements        = []
        self.currentFunctionName           = ""
        self.currentFunctionAccess         = ""
        self.currentFunctionStatic         = False
        self.currentFunctionBody           = ""
        self.currentBracketLevel           = 0
        self.currentNamespace              = ""
        self.previousNamespace             = ""
        self.listenForFunctionSignature    = False
        self.currentFunctionSignature      = ""
        self.listenForClassAttribute       = False
        self.currentClassAttribute         = ""
        self.ignoreUntilLineEnd            = False
        self.currentClassConstant          = ""
        self.listenForClassConstant        = False
        self.latestDocblock                = ""
        self.listenForPHPCode              = False
        self.isInsidePHPShortBlock         = False

    def traverseFolders(self, folder):
        for root, subFolders, files in os.walk(folder):
            for file in files:
                extension = file.split('.')[-1]

                try:
                    if (self.allowedExtensions.index(extension.lower()) >= 0):
                        self.allFilesList.append(os.path.join(root,file))
                except ValueError:
                    pass
                    # print(file + " skip")

            for subFolder in subFolders:
                if (subFolder != '.git' and subFolder != 'tests'):
                    self.traverseFolders(subFolder)

    def make_sure_path_exists(self, path):
        try:
            os.makedirs(path)
        except OSError as exception:
            pass

    def writeJSONOutput(self):
        if (self.getConfig('flag.processJSONOutput')):
            self.make_sure_path_exists(self.getConfig('logpath'))
            with open(self.getConfig('logpath') + 'index_folders.json', 'w+') as file:
                file.write(json.dumps(self.logData))


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