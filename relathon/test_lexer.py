# Copyright Peter Roger. All rights reserved.
#
# This file is part of relathon. Use of this source code is governed by
# the GPL license that can be found in the LICENSE file.

import unittest
from lexer import *
from tok import *
from relathon import Source
from errors import *

class TestLexer(unittest.TestCase):

    def checkTags(self, expected, text):
        source = Source('test', text)
        lexer = Lexer(source)
        tag = lexer.nextToken().tag
        while expected or tag != EOF:
            expects = expected.pop(0)
            self.assertEqual(expects, tag)
            tag = lexer.nextToken().tag

    def checkLexemes(self, expected, text):
        source = Source('test', text)
        lexer = Lexer(source)
        for expects in expected:
            lexeme = lexer.nextToken().lexeme
            self.assertEqual(expects, lexeme)

    def emitTokens(self, text):
        source = Source('test', text)
        lexer = Lexer(source)
        tok = lexer.nextToken()
        while tok.tag != EOF:
            tok = lexer.nextToken()

    def testKeywordTags(self):
        for tag, kw in [(FUNCDEF, "def"),(RETURN, "return"), (IF, "if"), (ELIF, "elif"),
        (ELSE, "else"), (WHILE, "while"), (CONTINUE, "continue"), (BREAK, "break"), (PASS, "pass"), (AND, "and"), (OR, "or"), (NOT, "not"), (TRUE, "True"), (FALSE, "False")]:
            self.checkTags([tag], kw)

    def testIndetifierLexemes(self):
        text = "func1(param1, param2):"
        self.checkLexemes(["func1", "(", "param1", ",", "param2", ")", ":", None], text)

    def testEmpty(self):
        text = ""
        self.checkTags([EOF], text)

    def testIndetifiers(self):
        for _id in ["_", "_a", "_A", "a", "A","Ba","bA","__","_a0","a_0"]:
            self.checkTags([IDENTIFIER], _id)

    def testNumerals(self):
        for tag, num in [(INTEGER, "0"),(INTEGER, "1"),(INTEGER, "99999"),(FLOAT, "0.1"),(FLOAT, ".1"),(FLOAT, ".9999"),(FLOAT, "15.456")]:
            self.checkTags([tag], num)

    def testOperators(self):
        for tag, op in [(STAR,"*"),(VBAR,"|"),(AMBER,"&"),(CIRCUMFLEX,"^"),
        (TILDE,"~"),(EQEQUAL,"=="),(NOTEQUAL,"!="),(LESSEQUAL,"<=")]:
            self.checkTags([tag], op)

    def testAssignmnetOperators(self):
        for tag, op in [(STAREQUAL,"*="),(VBAREQUAL,"|="),(AMBEREQUAL,"&="),(EQUAL,"=")]:
            self.checkTags([tag], op)

    def testSemi(self):
        text = ";"
        self.checkTags([SEMI], text)

    def testPars(self):
        text = "(())()"
        self.checkTags([LPAR, LPAR, RPAR, RPAR, LPAR, RPAR, EOF], text)

    def testSQB(self):
        text = "[][[]]"
        self.checkTags([LSQB, RSQB, LSQB, LSQB, RSQB, RSQB, EOF], text)

    def testNewline(self):
        text = "a\nb"
        self.checkTags([IDENTIFIER, NEWLINE, IDENTIFIER, EOF], text)

    def testBlanklines(self):
        text = " \n\t\n \t\n\t  \t \n#"
        self.checkTags([EOF], text)

    def testIndent(self):
        text = "    a"
        self.checkTags([INDENT, IDENTIFIER, EOF], text)

    def testNoBlankIndent(self):
        text = "\n\t\t\na"
        self.checkTags([IDENTIFIER, EOF], text)

    def testNoBlankOutdent(self):
        text = "\ta\n#"
        self.checkTags([INDENT, IDENTIFIER, NEWLINE, EOF], text)

    def testComment(self):
        text = "a #comment"
        self.checkTags([IDENTIFIER, EOF], text)

    def testCommentNewline(self):
        text = "a#comment\nb"
        self.checkTags([IDENTIFIER, NEWLINE, IDENTIFIER, EOF], text)

    def testCommentIndent(self):
        text = "    #comment\nb"
        self.checkTags([IDENTIFIER, EOF], text)

    def testEscapeNewline(self):
        text = "a\\\nb"
        self.checkTags([IDENTIFIER, IDENTIFIER, EOF], text)

    def testNestedNewline(self):
        text = "(a\n, b)"
        self.checkTags([LPAR, IDENTIFIER, COMMA, IDENTIFIER, RPAR, EOF], text)

    def testInvalidDedentation(self):
        text = "a\n\t\tb\n\tc"
        with self.assertRaises(IndentationException):
            self.emitTokens(text)

    def testInvalidChar(self):
        text = "$"
        with self.assertRaises(LexerException):
            self.emitTokens(text)

    def testSimpleAssignment(self):
        text = "a = b"
        self.checkTags([IDENTIFIER, EQUAL, IDENTIFIER, EOF], text)

    def testAugAssignment(self):
        text = "a *= b"
        self.checkTags([IDENTIFIER, STAREQUAL, IDENTIFIER, EOF], text)

    def testBoolInitialization(self):
        text = "a = True"
        self.checkTags([IDENTIFIER, EQUAL, TRUE, EOF], text)

    def testBitsInitializationInts(self):
        text = "a = [(1,0),(0,0)]"
        self.checkTags([IDENTIFIER, EQUAL, LSQB, LPAR, INTEGER, COMMA, INTEGER, RPAR, COMMA, LPAR, INTEGER, COMMA, INTEGER, RPAR, RSQB, EOF], text)

    def testBitsInitializationBools(self):
        text = "a = [(True,False),(False,False)]"
        self.checkTags([IDENTIFIER, EQUAL, LSQB, LPAR, TRUE, COMMA, FALSE, RPAR, COMMA, LPAR, FALSE, COMMA, FALSE, RPAR, RSQB, EOF], text)

    def testFuncdefStmt(self):
        text = "def foo():"
        self.checkTags([FUNCDEF, IDENTIFIER, LPAR, RPAR, COLON, EOF], text)

    def testFunction(self):
        text = "def bar(a, b):\n\treturn a"
        self.checkTags([FUNCDEF, IDENTIFIER, LPAR, IDENTIFIER, COMMA, IDENTIFIER,
        RPAR, COLON, NEWLINE, INDENT, RETURN, IDENTIFIER, EOF], text)

    def testFunctionTwoStmts(self):
        text = "def foo(a):\n\tb = a\n\treturn b"
        self.checkTags([FUNCDEF, IDENTIFIER, LPAR, IDENTIFIER, RPAR, COLON, NEWLINE, INDENT, IDENTIFIER, EQUAL, IDENTIFIER, NEWLINE, RETURN, IDENTIFIER, EOF], text)

    def testTwoFuncdefs(self):
        text = "def foo(a):\n\treturn a\n\n\n\ndef bar(b):\n\treturn b\n"
        self.checkTags([FUNCDEF, IDENTIFIER, LPAR, IDENTIFIER, RPAR, COLON,
                        NEWLINE, INDENT, RETURN, IDENTIFIER, NEWLINE, DEDENT,
                        FUNCDEF, IDENTIFIER, LPAR, IDENTIFIER, RPAR, COLON,
                        NEWLINE, INDENT, RETURN, IDENTIFIER, NEWLINE, EOF],
                        text)

if __name__ == '__main__':
    unittest.main()
