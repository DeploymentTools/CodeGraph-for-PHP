import re, os, io
from time import sleep
import json

class MethodExtractor():
    allFilesList      = []
    allowedExtensions = ['php']
    excludeFolders    = ['tests', '.git']
    outlineIndex      = []
    limitFiles        = 10000000000000000000000000
    cursorFiles       = 0

    listVariableKeywords  = ['public', 'private', 'protected', 'var', 'static']
    listConstantsKeywords = ['const']
    listFunctionAccess    = ['public', 'private', 'protected']
    listFunctionStatic    = ['static']

    FLAG_processMethodBody        = False
    FLAG_processMethodSignature   = False
    FLAG_processClassConstants    = False
    FLAG_processClassAttributes   = False
    FLAG_processJSONOutput        = False
    FLAG_processTestFileGenerator = True
    FLAG_manualPath               = True
    PATH_basePathRepository       = "/home/bogdana/workspace/avangate.secure.git/"
    PATH_logOutput                = 'logs';
    PATH_sourceRepository         = "secure"
    PATH_testRepository           = "tests-automatic"

    logData = []

    # transient flags
    currentClass                  = ""
    currentIsComment              = False
    currentIsMethod               = False
    currentIsStringInSingleQuotes = False
    currentIsStringInDoubleQuotes = False
    currentIsPHP                  = False
    previousChar                  = ""
    previous2Char                 = ""
    previousWord                  = ""
    previous2Word                 = ""
    previous3Word                 = ""
    previous4Word                 = ""
    previous5Word                 = ""
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

    def writeJSONOutput(self):
        if (self.FLAG_processJSONOutput):
            self.make_sure_path_exists(self.PATH_basePathRepository + '/' + self.PATH_logOutput)
            with open(os.path.join(self.PATH_basePathRepository + '/' + self.PATH_logOutput, 'index_folders.json'), 'w') as file:
                file.write(json.dumps(self.logData))

    def processMain(self):
        if (self.FLAG_processTestFileGenerator and self.FLAG_manualPath):
            self.make_sure_path_exists(self.PATH_basePathRepository + '/' + self.PATH_testRepository)

        for filepath in self.allFilesList:
            if (self.limitFiles == 0 or (self.limitFiles > 0 and self.limitFiles >= self.cursorFiles)):
                try:
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
        if (self.FLAG_processClassAttributes == False):
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
        if (self.FLAG_processClassConstants == False):
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

                                    if (functionSignature != False):
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
                                        logDataEntry['body']      = self.currentFunctionBody

                                        self.logData.append(logDataEntry)
                                        self.generateTestFile(logDataEntry)
                                        # print(logDataEntry)

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

    def registerCurrentChar(self, cursorCharacter):
        self.cursorCharacter = cursorCharacter

    def collectFunctionBody(self):
        if (self.FLAG_processMethodBody):
            if (((self.currentBracketLevel > 1) and (self.currentClassName != "")) or ((self.currentBracketLevel > 0) and (self.currentClassName == ""))):
                self.currentFunctionBody += self.cursorCharacter

    def getNamespace(self):
        namespace = self.currentNamespace
        if ((self.currentNamespace == "") & (self.previousNamespace != "")):
            namespace = self.previousNamespace
        return namespace

    def processFunctionSignature(self, originalSignature):
        if (self.FLAG_processMethodSignature == False):
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
                                        description = m[1]
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

                    if (description.strip() != ""):
                        signatureArgument['d'] = description

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

    def generateTestFile(self, entry):
        if (self.FLAG_processTestFileGenerator and self.FLAG_manualPath):
            # PATH_testRepository
            if (entry['class'] != ""):

                entryFile = entry['file'].replace(self.PATH_basePathRepository + '/' + self.PATH_sourceRepository, "")
                entryFileStructure = entryFile.split('/')

                try:
                    entryFileStructure.remove("")
                except ValueError:
                    pass

                entryFileStructure.pop()

                folder = self.PATH_basePathRepository + '/' + self.PATH_testRepository + '/' + '/'.join(entryFileStructure) + '/' + entry['class']
                self.make_sure_path_exists(folder)

                createBaseText = """<?php

class """+entry['class']+'_' + entry['name'] + """ extends PHPUnit_Framework_TestCase {

    public function testBlank(){
        $this->markTestSkipped('Auto generated method using a py scraper');
    }

}"""
                outputFile = folder + '/' + entry['name'] + 'Test.php'

                if (os.path.isfile(outputFile) == False):
                    print(folder + " | " + entry['name'] + 'Test.php' + " | " + entry['class'] + " | " + entry['name'] + " | " + entryFile + " | " + entry['line'])
                    with io.open(outputFile, 'w', encoding='utf-8') as f:
                        f.write(createBaseText)

                # print(entryFileStructure)
                # print(entry['namespace'])
                # print(entryFile)
                # print(entry['class'])
                # print(entry['name'])
                # print(createBaseText)

    def make_sure_path_exists(self, path):
        try:
            os.makedirs(path)
        except OSError as exception:
            pass