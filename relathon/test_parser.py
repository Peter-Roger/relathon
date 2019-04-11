# Copyright Peter Roger. All rights reserved.
#
# This file is part of relathon. Use of this source code is governed by
# the GPL license that can be found in the LICENSE file.

import unittest
import ast_node
from lexer import *
from parser import *
from tok import *
from relathon import Source
from errors import ParserException, IndentationException


class TestParserBase(unittest.TestCase):

    def parseFromSource(self, parseMethod, text):
        source = Source('test', text)
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parseMethod(parser)
        if not parser.nearEnd():
            raise ParserException(parser.location, "did not parse entire source")
        return result

    def checkParse(self, expected, parseMethod, text):
        result = self.parseFromSource(parseMethod, text)
        self.assertEqual(expected, result)

    def checkParseError(self, parseMethod, text, exception=ParserException):
        self.assertRaises(exception, self.parseFromSource, parseMethod, text)

    def checkParseNoError(self, parseMethod, text):
        try:
            self.parseFromSource(parseMethod, text)
        except Exception as e:
            self.fail("Raised {} unexpectedly: {}".format(type(e).__name__, str(e)))


class TestParser(TestParserBase):

    def testModuleEmpty(self):
        self.checkParse(astModule([]), Parser.module, "")

    # Expressions
    def testAtomicExpr(self):
        self.checkParse(astVariable(Tok(IDENTIFIER, "a")), Parser.expr, "a")

    def testAtomicParExpr(self):
        self.checkParse(astVariable(Tok(IDENTIFIER, "a")), Parser.expr, "(a)")

    def testTrue(self):
        self.checkParse(astBoolean(Tok(TRUE, "True")), Parser.expr, "True")

    def testFalse(self):
        self.checkParse(astBoolean(Tok(FALSE, "False")), Parser.expr, "False")

    def testParFalse(self):
        self.checkParse(astBoolean(Tok(FALSE, "False")), Parser.expr, "(False)")

    def testNegation(self):
        self.checkParse(astUnaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(TILDE, "~")), Parser.expr, "~a")

    def testParNegation(self):
        self.checkParse(astUnaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(TILDE, "~")), Parser.expr, "~(a)")

    def testTranspose(self):
        self.checkParse(astUnaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(CIRCUMFLEX, "^")), Parser.expr, "a^")

    def testParTranspose(self):
        self.checkParse(astUnaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(CIRCUMFLEX, "^")), Parser.expr, "(a)^")

    def testNegationNegation(self):
        self.checkParse(astUnaryOperation(astUnaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(TILDE, "~")), Tok(TILDE, "~")), Parser.expr, "~~a")

    def testNegationNegationNegation(self):
        self.checkParse(astUnaryOperation(astUnaryOperation(astUnaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(TILDE, "~")), Tok(TILDE, "~")), Tok(TILDE, "~")), Parser.expr, "~~~a")

    def testTransposeTranspose(self):
        self.checkParse(astUnaryOperation(astUnaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(CIRCUMFLEX, "^")), Tok(CIRCUMFLEX, "^")), Parser.expr, "a^^")

    def testTransposeTransposeTranspose(self):
        self.checkParse(astUnaryOperation(astUnaryOperation(astUnaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(CIRCUMFLEX, "^")), Tok(CIRCUMFLEX, "^")), Tok(CIRCUMFLEX, "^")), Parser.expr, "a^^^")

    def testNegationTranspose(self):
        self.checkParse(astUnaryOperation(astUnaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(CIRCUMFLEX, "^")), Tok(TILDE, "~")), Parser.expr, "~a^")

    def testNegationTransposeTranspose(self):
        self.checkParse(astUnaryOperation(astUnaryOperation(astUnaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(CIRCUMFLEX, "^")), Tok(CIRCUMFLEX, "^")), Tok(TILDE, "~")), Parser.expr, "~a^^")

    def testNegationNegationTranspose(self):
        self.checkParse(astUnaryOperation(astUnaryOperation(astUnaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(CIRCUMFLEX, "^")), Tok(TILDE, "~")), Tok(TILDE, "~")), Parser.expr, "~~a^")

    def testZero(self):
        self.checkParse(astInteger(Tok(INTEGER,"0")), Parser.integer, "0")

    def testOne(self):
        self.checkParse(astInteger(Tok(INTEGER,"1")), Parser.integer, "1")

    def testOrderedPairs1(self):
        self.checkParse(astOrderedPairs([(astInteger(Tok(INTEGER,"0")),astInteger(Tok(INTEGER,"1")))]), Parser.ordered_pairs, "[(0,1)]")

    def testOrderedPairs2(self):
        self.checkParse(astOrderedPairs([(astInteger(Tok(INTEGER,"0")),astInteger(Tok(INTEGER,"1"))),(astInteger(Tok(INTEGER,"2")),astInteger(Tok(INTEGER,"3")))]), Parser.ordered_pairs, "[(0,1),(2,3)]")

    def testOrderedPairsTrailingComma(self):
        self.checkParse(astOrderedPairs([(astInteger(Tok(INTEGER,"0")),astInteger(Tok(INTEGER,"1")))]), Parser.ordered_pairs, "[(0,1),]")

    def testComposition(self):
        self.checkParse(astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(STAR, "*"), astVariable(Tok(IDENTIFIER, "b"))), Parser.expr, "a * b")

    def testJoin(self):
        self.checkParse(astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(AMBER, "&"), astVariable(Tok(IDENTIFIER, "b"))), Parser.expr, "a & b")

    def testMeet(self):
        self.checkParse(astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(VBAR, "|"), astVariable(Tok(IDENTIFIER, "b"))), Parser.expr, "a | b")

    def testSubset(self):
        self.checkParse(astComparison(astVariable(Tok(IDENTIFIER, "a")), Tok(LESS, "<"), astVariable(Tok(IDENTIFIER, "b"))), Parser.comparison, "a < b")

    def testSubsetExpr(self):
        self.checkParse(astComparison(astVariable(Tok(IDENTIFIER, "a")), Tok(LESS, "<"), astBinaryOperation(astVariable(Tok(IDENTIFIER, "b")), Tok(STAR, "*"), astVariable(Tok(IDENTIFIER, "c")))), Parser.expr, "a < (b * c)")

    def testEquality(self):
        self.checkParse(astComparison(astVariable(Tok(IDENTIFIER, "a")), Tok(EQEQUAL, "=="), astVariable(Tok(IDENTIFIER, "b"))), Parser.comparison, "a == b")

    def testEqualityTrue(self):
        self.checkParse(astComparison(astVariable(Tok(IDENTIFIER, "a")), Tok(EQEQUAL, "=="), astBoolean(Tok(TRUE, "True"))), Parser.comparison, "a == True")

    def testEqualityFalse(self):
        self.checkParse(astComparison(astVariable(Tok(IDENTIFIER, "a")), Tok(EQEQUAL, "=="), astBoolean(Tok(FALSE, "False"))), Parser.comparison, "a == False")

    def testSuperset(self):
        self.checkParse(astComparison(astVariable(Tok(IDENTIFIER, "a")), Tok(GREATER, ">"), astVariable(Tok(IDENTIFIER, "b"))), Parser.comparison, "a > b")

    def testBinOpPar(self):
        self.checkParse(astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(STAR, "*"), astVariable(Tok(IDENTIFIER, "b"))), Parser.expr, "(a * b)")

    def testAtomBinOpExpr(self):
        self.checkParse(astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(STAR, "*"), astBinaryOperation(astVariable(Tok(IDENTIFIER, "b")), Tok(AMBER, "&"), astVariable(Tok(IDENTIFIER, "c")))), Parser.expr, "a * (b & c)")

    def testRightNestedPar(self):
        self.checkParse(astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(STAR, "*"), astBinaryOperation(astVariable(Tok(IDENTIFIER, "b")), Tok(AMBER, "&"),astBinaryOperation(astVariable(Tok(IDENTIFIER, "c")), Tok(VBAR, "|"), astVariable(Tok(IDENTIFIER, "d"))))), Parser.expr, "a * (b & (c | d))")

    def testLeftNestedPar(self):
        self.checkParse(astBinaryOperation(astBinaryOperation(astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(STAR, "*"), astVariable(Tok(IDENTIFIER, "b"))), Tok(AMBER, "&"), astVariable(Tok(IDENTIFIER, "c"))), Tok(VBAR, "|"), astVariable(Tok(IDENTIFIER, "d"))), Parser.expr, "((a * b) & c) | d")

    def testExprBinOpAtom(self):
        self.checkParse(astBinaryOperation(astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(STAR, "*"), astVariable(Tok(IDENTIFIER, "b"))), Tok(AMBER, "&"), astVariable(Tok(IDENTIFIER, "c"))), Parser.expr,
            "(a * b) & c")

    def testTranposeOnExpr(self):
        self.checkParse(astUnaryOperation(astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(STAR, "*"), astVariable(Tok(IDENTIFIER, "b"))), Tok(CIRCUMFLEX, "^")), Parser.expr, "(a * b)^")

    def testNegationOnExpr(self):
        self.checkParse(astUnaryOperation(astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(STAR, "*"), astVariable(Tok(IDENTIFIER, "b"))), Tok(TILDE, "~")), Parser.expr, "~(a * b)")

    def testAndCondition(self):
        self.checkParse(astBooleanOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(AND, "and"), astVariable(Tok(IDENTIFIER, "b"))), Parser.expr, "a and b")

    def testOrCondition(self):
        self.checkParse(astBooleanOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(OR, "or"), astVariable(Tok(IDENTIFIER, "b"))), Parser.expr, "a or b")

    def testAndOrCondition(self):
        self.checkParse(astBooleanOperation(astBooleanOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(AND, "and"), astVariable(Tok(IDENTIFIER, "b"))), Tok(OR, "or"), astVariable(Tok(IDENTIFIER, "c"))), Parser.expr, "a and b or c")

    def testOrAndCondition(self):
        self.checkParse(astBooleanOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(OR, "or"), astBooleanOperation(astVariable(Tok(IDENTIFIER, "b")), Tok(AND, "and"), astVariable(Tok(IDENTIFIER, "c")))), Parser.expr, "a or b and c")

    def testOrAndParCondition(self):
        self.checkParse(astBooleanOperation(astBooleanOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(OR, "or"), astVariable(Tok(IDENTIFIER, "b"))), Tok(AND, "and"), astVariable(Tok(IDENTIFIER, "c"))), Parser.expr, "(a or b) and c")

    def testNotExpr(self):
        self.checkParse(astUnaryOperation(astVariable(Tok(IDENTIFIER, 'a')), Tok(NOT, "not")), Parser.expr, "not a")

    def testNotAndExpr(self):
        self.checkParse(astBooleanOperation(astUnaryOperation(astVariable(Tok(IDENTIFIER, 'a')), Tok(NOT, "not")), Tok(AND, "and"), astVariable(Tok(IDENTIFIER, "b"))), Parser.expr, "not a and b")

    def testNotOrExpr(self):
        self.checkParse(astBooleanOperation(astUnaryOperation(astVariable(Tok(IDENTIFIER, 'a')), Tok(NOT, "not")), Tok(OR, "or"), astVariable(Tok(IDENTIFIER, "b"))), Parser.expr, "not a or b")

    def testNotParAndExpr(self):
        self.checkParse(astUnaryOperation(astBooleanOperation(astVariable(Tok(IDENTIFIER, 'a')), Tok(AND, "and"), astVariable(Tok(IDENTIFIER, "b"))), Tok(NOT, "not")), Parser.expr, "not (a and b)")

    def testNotParOrExpr(self):
        self.checkParse(astUnaryOperation(astBooleanOperation(astVariable(Tok(IDENTIFIER, 'a')), Tok(OR, "or"), astVariable(Tok(IDENTIFIER, "b"))), Tok(NOT, "not")), Parser.expr, "not (a or b)")

    def testSimpleTernaryOperation(self):
        self.checkParse(astTernaryOperation(astVariable(Tok(IDENTIFIER, 'a')), astVariable(Tok(IDENTIFIER, 'a')), astVariable(Tok(IDENTIFIER, 'b'))), Parser.expr, "a if a else b")

    def testTernaryOperation(self):
        self.checkParse(astTernaryOperation(astVariable(Tok(IDENTIFIER, "a")), astComparison(astVariable(Tok(IDENTIFIER, "a")), Tok(NOTEQUAL, "!="), astVariable(Tok(IDENTIFIER, "b"))), astVariable(Tok(IDENTIFIER, 'c'))), Parser.expr, "a if a != b else c")

    def testFunctionCall(self):
        self.checkParse(astFunctionCall(astVariable(Tok(IDENTIFIER, "foo")), []), Parser.expr, "foo()")

    def testFunctionCallArg(self):
        self.checkParse(astFunctionCall(astVariable(Tok(IDENTIFIER, "foo")), [astVariable(Tok(IDENTIFIER, "a"))]), Parser.expr, "foo(a)")

    def testFunctionCallArgs(self):
        self.checkParse(astFunctionCall(astVariable(Tok(IDENTIFIER, "foo")), [astVariable(Tok(IDENTIFIER, "a")),astVariable(Tok(IDENTIFIER, "b"))]), Parser.expr, "foo(a,b)")

    def testFunctionCallIntArg(self):
        self.checkParse(astFunctionCall(astVariable(Tok(IDENTIFIER, "foo")), [astInteger(Tok(INTEGER, 4))]), Parser.expr, "foo(4)")

    def testFunctionCallFloatArg(self):
        self.checkParse(astFunctionCall(astVariable(Tok(IDENTIFIER, "foo")), [astFloat(Tok(FLOAT, 1.0))]), Parser.expr, "foo(1.0)")

    def testFunctionCallCharArg(self):
        self.checkParse(astFunctionCall(astVariable(Tok(IDENTIFIER, "foo")), [astChar(Tok(CHAR, "'c'"))]), Parser.expr, "foo('c')")

    def testFunctionCallArgsTrailingComma(self):
        self.checkParse(astFunctionCall(astVariable(Tok(IDENTIFIER, "foo")), [astVariable(Tok(IDENTIFIER, "a")),astVariable(Tok(IDENTIFIER, "b"))]), Parser.expr, "foo(a,b,)")

    def testFunctionCallBinOpArg(self):
        self.checkParse(astFunctionCall(astVariable(Tok(IDENTIFIER, "foo")), [astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(STAR, "*"), astVariable(Tok(IDENTIFIER, "b")))]), Parser.expr, "foo(a * b)")

    def testFunctionCallNested(self):
        self.checkParse(astFunctionCall(astVariable(Tok(IDENTIFIER, "foo")), [astFunctionCall(astVariable(Tok(IDENTIFIER, "bar")), [astVariable(Tok(IDENTIFIER, "a"))])]), Parser.expr, "foo(bar(a))")

    # Statements
    def testAssignment(self):
        self.checkParse(astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(EQUAL, "="), astVariable(Tok(IDENTIFIER,"b"))), Parser.expr_stmt, "a = b")

    def testAssignmentTrailingSemi(self):
        self.checkParse(astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(EQUAL, "="), astVariable(Tok(IDENTIFIER,"b"))), Parser.simple_stmt, "a = b;")

    def testAssignmentMultiLineNoTrailingSemi(self):
        self.checkParse(astSuite([astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(EQUAL, "="), astVariable(Tok(IDENTIFIER,"b"))), astAssignment(astVariable(Tok(IDENTIFIER, "c")), Tok(EQUAL, "="), astVariable(Tok(IDENTIFIER,"d")))]), Parser.simple_stmt, "a = b; c = d")

    def testAssignmentMultiLineTrailingSemi(self):
        self.checkParse(astSuite([astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(EQUAL, "="), astVariable(Tok(IDENTIFIER,"b"))), astAssignment(astVariable(Tok(IDENTIFIER, "c")), Tok(EQUAL, "="), astVariable(Tok(IDENTIFIER,"d")))]), Parser.simple_stmt, "a = b; c = d;")

    def testCompAugAssignment(self):
        self.checkParse(astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(STAREQUAL, "*="), astVariable(Tok(IDENTIFIER,"b"))), Parser.expr_stmt, "a *= b")

    def testJoinAugAssignment(self):
        self.checkParse(astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(AMBEREQUAL, "&="), astVariable(Tok(IDENTIFIER,"b"))), Parser.expr_stmt, "a &= b")

    def testMeetAugAssignment(self):
        self.checkParse(astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(VBAREQUAL, "|="), astVariable(Tok(IDENTIFIER,"b"))), Parser.expr_stmt, "a |= b")

    def testNegationOnExprAssignment(self):
        self.checkParse(astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(EQUAL, "="), astUnaryOperation(astBinaryOperation(astVariable(Tok(IDENTIFIER, "b")), Tok(STAR, "*"), astVariable(Tok(IDENTIFIER, "c"))), Tok(TILDE, "~"))), Parser.expr_stmt, "a = ~(b * c)")

    def testTransposeOnExprAssignment(self):
        self.checkParse(astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(EQUAL, "="), astUnaryOperation(astBinaryOperation(astVariable(Tok(IDENTIFIER, "b")), Tok(STAR, "*"), astVariable(Tok(IDENTIFIER, "c"))), Tok(CIRCUMFLEX, "^"))), Parser.expr_stmt, "a = (b * c)^")

    def testTernaryAssignment(self):
        self.checkParse(astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(EQUAL, "="), astTernaryOperation(astVariable(Tok(IDENTIFIER, "b")), astComparison(astVariable(Tok(IDENTIFIER, "b")), Tok(NOTEQUAL, "!="), astVariable(Tok(IDENTIFIER, "c"))), astVariable(Tok(IDENTIFIER, 'd')))), Parser.expr_stmt, "a = b if b != c else d")

    def testEmptyBitsInit(self):
        self.checkParse(astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(EQUAL, "="), astOrderedPairs([])), Parser.expr_stmt, "a = []")

    def testBitsInit(self):
        self.checkParse(astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(EQUAL, "="), astOrderedPairs([(astInteger(Tok(INTEGER,"0")), astInteger(Tok(INTEGER,"1"))),(astInteger(Tok(INTEGER,"2")), astInteger(Tok(INTEGER,"3")))])), Parser.expr_stmt, "a = [(0,1),(2,3)]")

    def testBitsInitTrailingComma(self):
        self.checkParse(astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(EQUAL, "="), astOrderedPairs([(astInteger(Tok(INTEGER,"0")), astInteger(Tok(INTEGER,"1"))),])), Parser.expr_stmt, "a = [(0,1),]")

    def testInvalidBitsEmpty(self):
        self.checkParseError(ParserException, "[()]")

    def testInvalidBitsPartial(self):
        self.checkParseError(ParserException, "[(1,)]")

    def testInvalidBits2ndPartial(self):
        self.checkParseError(ParserException, "[(1,1),()]")

    # Function Definitions
    def testFuncDefNoParams(self):
        self.checkParse(astFunctionDefinition(astVariable(Tok(IDENTIFIER, 'foo')), [], astSuite([astPassStatement()])), Parser.functionDef, "def foo():\n\tpass")

    def testSingleFunction(self):
        self.checkParse(astModule([astFunctionDefinition(astVariable(Tok(IDENTIFIER, "foo")), [], astSuite([astPassStatement()]))]), Parser.module, "def foo():\n\tpass")

    def testTwoFunctions(self):
        self.checkParse(astModule([astFunctionDefinition(astVariable(Tok(IDENTIFIER, "foo")), [], astSuite([astPassStatement()])),astFunctionDefinition(astVariable(Tok(IDENTIFIER, "bar")), [], astSuite([astPassStatement()]))]), Parser.module, "def foo():\n\tpass\n\ndef bar():\n\tpass")

    def testFunctionNewlines(self):
        self.checkParse(astModule([astFunctionDefinition(astVariable(Tok(IDENTIFIER, "foo")), [], astSuite([astPassStatement()]))]), Parser.module, "def foo():\n\n\n\tpass")

    def testFunctionSingleParam(self):
        self.checkParse(astModule([astFunctionDefinition(astVariable(Tok(IDENTIFIER, "foo")), [astParameter(astVariable(Tok(IDENTIFIER, 'a')))], astSuite([astPassStatement()]))]), Parser.module, "def foo(a):\n\tpass")

    def testFunctionDoubleParam(self):
        self.checkParse(astModule([astFunctionDefinition(astVariable(Tok(IDENTIFIER, "foo")), [astParameter(astVariable(Tok(IDENTIFIER, 'a'))), astParameter(astVariable(Tok(IDENTIFIER, 'b')))], astSuite([astPassStatement()]))]), Parser.module, "def foo(a,b):\n\tpass")

    def testFunctionSingleParamTrailingComma(self):
        self.checkParse(astModule([astFunctionDefinition(astVariable(Tok(IDENTIFIER, "foo")), [astParameter(astVariable(Tok(IDENTIFIER, 'a')))], astSuite([astPassStatement()]))]), Parser.module, "def foo(a,):\n\tpass")

    def testFuncDefReturnAtom(self):
        self.checkParse(astFunctionDefinition(astVariable(Tok(IDENTIFIER, 'foo')), [astParameter(astVariable(Tok(IDENTIFIER, 'a')))], astSuite([astReturnStatement(astVariable(Tok(IDENTIFIER, 'a')))])),Parser.functionDef,"def foo(a):\n\treturn a")

    def testFuncDefStmts(self):
        self.checkParse(astFunctionDefinition(astVariable(Tok(IDENTIFIER, 'foo')), [astParameter(astVariable(Tok(IDENTIFIER, 'a')))], astSuite([astAssignment(astVariable(Tok(IDENTIFIER, "b")), Tok(EQUAL, "="), astVariable(Tok(IDENTIFIER,"a"))),astReturnStatement(astVariable(Tok(IDENTIFIER, "b")))])), Parser.functionDef,"def foo(a):\n\tb = a\n\treturn b")

    def testFuncReturnExpr(self):
        self.checkParse(astFunctionDefinition(astVariable(Tok(IDENTIFIER, "foo")), [astParameter(astVariable(Tok(IDENTIFIER, "a"))), astParameter(astVariable(Tok(IDENTIFIER, "b")))], astSuite([astReturnStatement(astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(STAR, "*"), astVariable(Tok(IDENTIFIER, "b"))))])), Parser.functionDef, "def foo(a, b):\n\treturn a * b")

    def testSingleLineFunc(self):
        self.checkParse(astFunctionDefinition(astVariable(Tok(IDENTIFIER, 'foo')), [astParameter(astVariable(Tok(IDENTIFIER, 'a')))], astSuite([astReturnStatement(astVariable(Tok(IDENTIFIER, 'a')))])), Parser.functionDef,"def foo(a) = a")

    def testInvalidFuncDef(self):
        self.checkParseError(Parser.functionDef, "def ()")

    def testInvalidFuncDef2(self):
        self.checkParseError(Parser.functionDef, "def f();\n\tpass")

    def testInvalidFuncDef3(self):
        self.checkParseError(Parser.functionDef, "def f(,):\n\tpass")

    def testInvalidSingleLineFuncDef(self):
        self.checkParseError(Parser.functionDef, "def f() = return")

    # Control Flow
    def testPassStmt(self):
        self.checkParse(astPassStatement(), Parser.statement, "pass")

    def testContinueStmt(self):
        self.checkParseError(Parser.control_stmt, "continue", exception=ParserException)

    def testBreakStmt(self):
        self.checkParseError(Parser.control_stmt, "break", exception=ParserException)

    def testWhileSingleStmt(self):
        self.checkParse(astWhileStatement(astComparison(astVariable(Tok(IDENTIFIER, "a")),Tok(NOTEQUAL, "!="), astVariable(Tok(IDENTIFIER, "b"))), astSuite([astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(EQUAL, "="), astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")),Tok(VBAR, "|"), astVariable(Tok(IDENTIFIER, "b"))))]), None), Parser.while_stmt, "while a != b:\n\ta = a | b")

    def testWhileDoubleStmt(self):
        self.checkParse(astWhileStatement(astComparison(astVariable(Tok(IDENTIFIER, "a")),Tok(NOTEQUAL, "!="), astVariable(Tok(IDENTIFIER, "b"))), astSuite([astAssignment(astVariable(Tok(IDENTIFIER, "a")), Tok(EQUAL, "="), astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")),Tok(VBAR, "|"),astVariable(Tok(IDENTIFIER, "b")))), astAssignment(astVariable(Tok(IDENTIFIER, "b")), Tok(EQUAL, "="), astBinaryOperation(astVariable(Tok(IDENTIFIER, "a")), Tok(STAR, "*"), astVariable(Tok(IDENTIFIER, "b"))))]), None), Parser.while_stmt, "while a != b:\n\ta = a | b\n\tb = a * b")

    def testIfStmt(self):
        self.checkParse(astIfStatement(astVariable(Tok(IDENTIFIER, "a")), astSuite([astPassStatement()]),[],[]), Parser.statement, "if a:\n\tpass")

    def testIfStmtNestedIfStmt(self):
        self.checkParse(astIfStatement(astVariable(Tok(IDENTIFIER, "a")), astSuite([astIfStatement(astVariable(Tok(IDENTIFIER, "b")), astSuite([astPassStatement()]),[], [])]), [], []), Parser.statement, "if a:\n\tif b:\n\t\tpass")

    def testIfElifStmt(self):
        self.checkParse(astIfStatement(astVariable(Tok(IDENTIFIER, "a")), astSuite([astPassStatement()]), [astElifStatement(astVariable(Tok(IDENTIFIER, "b")), astSuite([astPassStatement()]))], []), Parser.statement, "if a:\n\tpass\nelif b:\n\tpass")

    def testIfElifElifStmt(self):
        self.checkParse(astIfStatement(astVariable(Tok(IDENTIFIER, "a")), astSuite([astPassStatement()]), [astElifStatement(astVariable(Tok(IDENTIFIER, "b")), astSuite([astPassStatement()])), astElifStatement(astVariable(Tok(IDENTIFIER, "c")), astSuite([astPassStatement()]))], []), Parser.statement, "if a:\n\tpass\nelif b:\n\tpass\nelif c:\n\tpass")

    def testIfElseII(self):
        self.checkParse(astIfStatement(astVariable(Tok(IDENTIFIER, "a")), astSuite([astPassStatement()]), [], astSuite([astPassStatement(),astPassStatement()])), Parser.statement, "if a:\n\tpass\nelse:\n\tpass\n\tpass")

    def testIfElifElse(self):
        self.checkParse(astIfStatement(astVariable(Tok(IDENTIFIER, "a")), astSuite([astPassStatement()]), [astElifStatement(astVariable(Tok(IDENTIFIER, "b")), astSuite([astPassStatement()]))], astSuite([astPassStatement()])), Parser.statement, "if a:\n\tpass\nelif b:\n\tpass\nelse:\n\tpass")

    # Indentation
    def testBlankLines(self):
        self.checkParseNoError(Parser.module, "\n\n\n\n")

    def testWhiteSpaceBeforeNewline(self):
        self.checkParseNoError(Parser.module, "\ndef f():    \n\tpass")

    def testWhiteIrregularBlankLineIndentation(self):
        self.checkParseNoError(Parser.module, "\ndef f():  \n   \n\tpass")

    def testUnexpectedIndent(self):
        self.checkParseError(Parser.module, "\tpass", exception=IndentationException)

    def testExpectedIndentFuncDef(self):
        self.checkParseError(Parser.functionDef, "def f(): pass", exception=IndentationException)

    def testExpectedIndentFuncDef2(self):
        self.checkParseError(Parser.functionDef, "def f():\npass", exception=IndentationException)

    def testUnexpectedIndentFuncDef(self):
        self.checkParseError(Parser.functionDef, "def f():\n pass\n  pass", exception=IndentationException)

    def testUnexpectedDedentFuncDef(self):
        self.checkParseError(Parser.functionDef, "def f():\n  pass\n pass", exception=IndentationException)




if __name__ == '__main__':
    def _astCtor(cls):
        def _ctor(*args):
            args = (NoLoc,) + args
            try:
                return cls(*args)
            except TypeError as e:
                print(cls)
                print(e)
                return
        return _ctor

    def _tokCtor():
        def _ctor(*args):
            args += (NoLoc,)
            return Token(*args)
        return _ctor

    for k, v in ast.__dict__.items():
        if type(v) is type and issubclass(v, ast_node.ASTNode):
            globals()["ast" + k] = _astCtor(v)

    globals()["Tok"] = _tokCtor()
    unittest.main()