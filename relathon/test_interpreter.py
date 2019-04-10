# Copyright Peter Roger. All rights reserved.
#
# This file is part of relathon. Use of this source code is governed by
# the GPL license that can be found in the LICENSE file.

import unittest
import ast_node
from lexer import *
from parser import *
from interpreter import Interpreter
from tok import *
from functions import *
from relathon import Source
from pyrel import PyrelContext, Relation
from errors import *


class TestInterpreterBase(unittest.TestCase):

    def setUp(self):
        self.context = PyrelContext()
        self.intrpr = Interpreter(self.context)

    def tearDown(self):
        del self.context

    def interpretFromSource(self, text):
        source = Source("<test>", text)
        lexer = Lexer(source)
        parser = Parser(lexer)
        ast = parser.parse(Parser.module)
        self.intrpr.visit(ast)

    def checkInterpret(self, name, expected, text):
        self.interpretFromSource(text)
        env = self.intrpr.currentEnv
        result = env.resolve(name)
        self.assertEqual(expected, result)

    def checkInterpreterError(self, exception, text):
        self.assertRaises(exception, self.interpretFromSource, text)

    def makeRelation(self, **kwargs):
        rel = self.context.new(**kwargs)
        return TestRelation(self, rel)

    def makeFunction(self, **kwargs):
        return TestFunction(self, **kwargs)


class TestInterpreter(TestInterpreterBase):

    # Relations
    def testBasicRelation(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(1,1)")

    def testRelationBit(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(0,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(3,3,[(0,2)])")

    def testRelationBits(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(1,1),(0,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "bits = [(1,1),(0,2)]\nr = new(3,3,bits)")

    def testFalse(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = False")

    def testTrue(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = True")

    def testNotTrue(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = not True")

    def testNotFalse(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = not False")

    def testAndTrueTrue(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = True and True")

    def testAndTrueFalse(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = True and False")

    def testAndFalseTrue(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = False and True")

    def testAndFalseFalse(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = False and False")

    def testOrTrueTrue(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = True or True")

    def testOrTrueFalse(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = True or False")

    def testOrFalseTrue(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = False or True")

    def testAndFalseFalse(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = False or False")

    def testComplement(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = ~True")

    def testTranspose(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 2
        kwargs['cols'] = 2
        kwargs['bits'] = [(1,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(2,2,[(0,1)])^")

    def testMeet(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 2
        kwargs['cols'] = 2
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(2,2,[(0,0),(0,1)]) & new(2,2,[(0,0),(1,0)])")

    def testJoin(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 2
        kwargs['cols'] = 2
        kwargs['bits'] = [(0,0),(0,1),(1,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(2,2,[(0,0),(0,1)]) | new(2,2,[(0,0),(1,0)])")

    def testComposition(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 4
        kwargs['cols'] = 4
        kwargs['bits'] = [(0,3),(2,3)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(4,4,[(0,1),(2,3)]) * new(4,4,[(1,3),(3,3)])")

    def testEquals(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(2,2,[(0,1)]) == new(2,2,[(0,1)])")

    def testUnEquals(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(2,2,[(0,0)]) == new(2,2,[(0,1)])")

    def testNotEquals(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(2,2,[(0,0)]) != new(2,2,[(0,1)])")

    def testUnNotEquals(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(2,2,[(0,1)]) != new(2,2,[(0,1)])")

    def testisSubset(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(2,2,[(0,1)]) < L(2,2)")

    def testisStrictSubset(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(2,2,[(0,1)]) <= L(2,2)")

    def testUnIsStrictSubset(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = L(2,2) <= L(2,2)")

    def testisSuperset(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = L(2,2) > new(2,2,[(0,1)])")

    def testUnIsStrictSuperset(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = L(2,2) >= L(2,2)")

    def testUnionEquals(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(0,0),(1,1)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(3,3,[(0,0)])\nr |= new(3,3,[(1,1)])")

    def testIntersectionEquals(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(1,1)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(3,3,[(1,0),(1,1)])\nr &= I(3,3)")

    def testCompositionEquals(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(0,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(3,3,[(0,1)])\nr *= new(3,3,[(1,2)])")

    # control flow
    def testIfStmt(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "if True:\n\tr = True")

    def testIfElseStmt(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "if False:\n\tr = False\nelse:\n\tr = True")

    def testIfElifElseStmt(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "if False:\n\tr = False\nelif True:\n\tr = True\nelse:\n\tr = False")

    def testIfElifElifElseStmt(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "if False:\n\tr = False\nelif False:\n\tr = False\nelif True:\n\tr = True\nelse:\n\tr = False")

    def testWhile(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(0,0),(0,1),(1,1),(2,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "def ftc(R):\n\tP = I(R)\n\tQ = O(R)\n\tS = P\n\twhile Q != S:\n\t\tP = P * R\n\t\tQ = S\n\t\tS = S | P\n\treturn S\nr=ftc(new(3,3,[(0,1)]))")

    # import

    def testImport(self):
        import tempfile
        import os.path
        from pathlib import Path
        import tracemalloc
        tracemalloc.start()
        path = os.path.dirname(os.path.realpath(__file__))
        snapshot1 = tracemalloc.take_snapshot()
        with tempfile.NamedTemporaryFile(mode='r+', dir=path, suffix='.rel') as f:
            name = 'r'
            kwargs = {}
            kwargs['rows'] = 3
            kwargs['cols'] = 3
            kwargs['bits'] = [(0,0)]
            rel = self.makeRelation(**kwargs)
            module = Path(os.path.basename(f.name)).with_suffix('')
            f.write("r = new(3,3,[(0,0)])")
            f.seek(0)
            self.checkInterpret(name, rel, "import {}".format(module))
            f.close()

    # Inbuilt functions
    def testNewFunctionFromRel(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(0,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(new(3,3),[(0,2)])")

    def testRelationCopy(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(0,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "s = new(3,3,[(0,2)])\nr = copy(s)")

    def testRelationRandomProb99(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(0,0),(0,1),(0,2),
                          (1,0),(1,1),(1,2),
                          (2,0),(2,1),(2,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = random(3,3,0.99)")

    def testRelationRandomProb01(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = random(3,3,0.01)")

    def testRelationSet(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(0,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(3,3)\nset(r,[(0,2)])")

    def testRelationUnset(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = new(3,3,[(0,2)])\nunset(r,[(0,2)])")

    def testSetChars(self):
        from io import StringIO
        import sys
        _stdout = sys.stdout
        sys.stdout = temp_stdout = StringIO()

        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 2
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.interpretFromSource("setchars('!','@')\nprint(new(1,2,[(0,0)]))")
        sys.stdout = _stdout
        self.assertEqual("!@",temp_stdout.getvalue().rstrip())

    def testEmptyRelation(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = O(3,3)")

    def testIdentityRelation(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(0,0),(1,1),(2,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = I(3,3)")

    def testUniversalRelation(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(0,0),(0,1),(0,2),
                          (1,0),(1,1),(1,2),
                          (2,0),(2,1),(2,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = L(3,3)")

    def testVector1(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(0,0),(0,1),(0,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = vec(3,3)")

    def testVector2(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(1,0),(1,1),(1,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = vec(3,3,1)")

    def testVector3(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(2,0),(2,1),(2,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = vec(3,3,2)")

    def testVectorRelTwo(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 3
        kwargs['cols'] = 3
        kwargs['bits'] = [(2,0),(2,1),(2,2)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "s=new(3,3)\nr = vec(s,2)")


    # Custom Functions
    def testBasicFunction(self):
        kwargs = {}
        name = 'f'
        kwargs['name'] = name
        kwargs['parameters'] = []
        kwargs['statements'] = astSuite([astPassStatement()])
        func = self.makeFunction(**kwargs)
        self.checkInterpret(kwargs['name'], func, "def f():\n\tpass")

    def testFunctionParam(self):
        kwargs = {}
        name = 'f'
        kwargs['name'] = name
        kwargs['parameters'] = ['a']
        kwargs['statements'] = astSuite([astPassStatement()])
        func = self.makeFunction(**kwargs)
        self.checkInterpret(name, func, "def f(a):\n\tpass")

    def testFunctionParams(self):
        kwargs = {}
        name = 'f'
        kwargs['name'] = name
        kwargs['parameters'] = ['a','b']
        kwargs['statements'] = astSuite([astPassStatement()])
        func = self.makeFunction(**kwargs)
        self.checkInterpret(kwargs['name'], func, "def f(a,b):\n\tpass")

    def testFunctionReturnBasic(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "def f(a):\n\treturn a\nr = f(new(1,1))")

    def testFunctionReturnBasic2(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "def f(a):\n\treturn a\nr = f(new(1,1,[(0,0)]))")

    def testFunctionReturnComplementExpr(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "def f(a):\n\treturn ~a\nr = f(new(1,1))")

    def testFunctionReturnTransposeExpr(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 2
        kwargs['cols'] = 2
        kwargs['bits'] = [(0,1)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "def f(a):\n\treturn a^\nr = f(new(2,2,[(1,0)]))")

    def testFunctionMultiline(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 2
        kwargs['cols'] = 2
        kwargs['bits'] = [(0,0),(0,1)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "def f():\n\ta=new(2,2,[(0,0),(0,1)])\n\treturn a\nr=f()")

    def testBasicSingleLineFunction(self):
        kwargs = {}
        name = 'f'
        kwargs['name'] = name
        kwargs['parameters'] = ['a']
        kwargs['statements'] = astSuite([astReturnStatement(astVariable(Tok(IDENTIFIER, 'a')))])
        func = self.makeFunction(**kwargs)
        self.checkInterpret(kwargs['name'], func, "def f(a) = a")

    def testBasicSingleLineFunction2(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 2
        kwargs['cols'] = 2
        kwargs['bits'] = [(0,0),(0,1)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "def f(a) = a\nr = f(new(2,2,[(0,0),(0,1)]))")

    def testTernaryExpressionTrue(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = [(0,0)]
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = True if True else False")

    def testTernaryExpressionFalse(self):
        name = 'r'
        kwargs = {}
        kwargs['rows'] = 1
        kwargs['cols'] = 1
        kwargs['bits'] = []
        rel = self.makeRelation(**kwargs)
        self.checkInterpret(name, rel, "r = True if not True else False")

    # Exceptions
    def testNameUndefined(self):
        self.checkInterpreterError(NameException,"a")

    def testRelOrInt(self):
        self.checkInterpreterError(TypeException,"True or 5")

    def testOrderedPairsCompOrderedPairs(self):
        self.checkInterpreterError(TypeException,"[] * []")

    def testOrderedPairsCompChar(self):
        self.checkInterpreterError(TypeException,"[] * 'a'")

    def testOrderedPairsJoinFloat(self):
        self.checkInterpreterError(TypeException,"[] | 0.4")

    def testOrderedPairsMeetInt(self):
        self.checkInterpreterError(TypeException,"[] & 5")

    def testIntAndInt(self):
        self.checkInterpreterError(TypeException,"5 and 4")

    def testComplementFloat(self):
        self.checkInterpreterError(TypeException,"~0.5")

    def testTransposeInt(self):
        self.checkInterpreterError(TypeException,"5^")

    def testRelNotCallable(self):
        self.checkInterpreterError(TypeException,"a = new(1,1)\na()")

    def testBitsNotCallable(self):
        self.checkInterpreterError(TypeException,"a = [(1,1)]\na()")

    def testExceededArity(self):
        self.checkInterpreterError(ArityException,"new(1,2,3,4)")

    def testSubceedArity(self):
        self.checkInterpreterError(ArityException,"new()")

    def testIfConditionalNotBool(self):
        self.checkInterpreterError(TypeException,"if []:\n\tpass")

    def testElifConditionalNotBool(self):
        self.checkInterpreterError(TypeException,"if False:\n\tpass\nelif []:\n\tpass")

    def testWhileConditionalNotBool(self):
        self.checkInterpreterError(TypeException,"while []:\n\tpass")

    def testModuleNotFound(self):
        self.checkInterpreterError(ModuleNotFoundException,"import x")






class TestObj:

    def __init__(self, test, **kwargs):
        super().__init__(**kwargs)
        self.test = test


class TestRelation(TestObj, Relation):

    def __init__(self, test, rel, **kwargs):
        kwargs = {}
        for k,v in rel.__dict__.items():
            kwargs[k] = v
        del kwargs['rows']
        del kwargs['cols']
        self.pyrel = rel # keep a reference to prevent mem deallocation
        super().__init__(test, **kwargs)

    def __eq__(self, other):
        if self.__class__.__bases__[1] is not other.__class__:
            return False
        return self.equals(other)


class TestFunction(TestObj, Function):

    def __eq__(self, other):
        if self.__class__.__bases__[1] is not other.__class__:
            return False
        if self.name != other.name:
            return False
        props = self.parameters + list(self.statements)
        otherProps = other.parameters + list(other.statements)
        if len(props) != len(otherProps):
            return False
        for prop, otherprop in zip(props, otherProps):
            if prop != otherprop:
                self.test.assertEqual(prop, otherprop)
                return False
        return True

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