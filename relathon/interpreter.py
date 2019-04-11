# Copyright Peter Roger. All rights reserved.
#
# This file is part of relathon. Use of this source code is governed by
# the GPL license that can be found in the LICENSE file.

"""This module describes Relathon's tree walk interpreter. The interpreter executes the abstract-syntax tree by walking (or visiting) each tree node and making descisions based upon the node type and data."""

import relathon
from ast_node import BinaryOperation
from environment import Environment
from functions import *
from tok import *
from errors import ArityException, NameException, RelationException, TypeException, ModuleNotFoundException
from pyrel import PyrelContext, Relation, PyrelException
from collections import namedtuple, OrderedDict


class Return(Exception):

    def __init__(self, value):
        self.value = value


class Continue(Exception):
    pass


class Break(Exception):
    pass


class Visitor(object):
    """Base Class to the Tree-Walking node visitor interpreter."""

    def visit(self, node):
        """Determines which interpreter method to call based on the
        type of tree node."""
        className = node.__class__.__name__
        methodName = self.getMethodName(className)
        if hasattr(self, methodName):
            method = getattr(self, methodName)
            result = method(node)
        else:
            result = self.visitDefault(node)
        return result

    def getMethodName(self, className):
        return "visit" + className

    def visitDefault(self, node):
        raise NotImplementedError(node.__class__.__name__)


class Interpreter(Visitor):
    """A tree walker interpreter with a method for each AST node type."""

    LITERAL = int, float, str, bool

    def __init__(self, context=None):
        self.context = context if context else PyrelContext()
        builtins_ = Environment(name="_builtins_")
        self.current_env = builtins_
        self._define_builtins()

        self.callstack = []

    def _define_builtins(self):
        """Initialise the builtins and global environments."""
        self.TrueRel = self.context.new(1,1,[(0,0)])
        self.FalseRel = self.context.new(1,1)

        if self.current_env.name == "_builtins_":
            builtins_ = self.current_env
            builtins_.define("new", NewFunction(self.context))
            builtins_.define("copy", CopyFunction(self.context))
            builtins_.define("random", RandomFunction(self.context))
            builtins_.define("vec", VectorFunction(self.context))
            builtins_.define("set", SetBitsFunction())
            builtins_.define("unset", UnsetBitsFunction())
            builtins_.define("setchars", SetCharsFunction())
            builtins_.define("print", PrintFunction())
            builtins_.define("O", EmptyFunction(self.context))
            builtins_.define("L", UniversalFunction(self.context))
            builtins_.define("I", IdentityFunction(self.context))
            builtins_.define("empty", IsEmptyFunction(self.TrueRel, self.FalseRel))


            self.operatorToOperation = {
                STAR: Relation.composition,
                VBAR: Relation.join,
                OR: Relation.join,
                AMBER: Relation.meet,
                AND: Relation.meet,
                EQEQUAL: Relation.equals,
                NOTEQUAL: Relation.notEquals,
                LESSEQUAL: Relation.isSubset,
                GREATEREQUAL: Relation.isSuperset,
                GREATER: Relation.isStrictSuperset,
                LESS: Relation.isStrictSubset,
                CIRCUMFLEX: Relation.transpose,
                TILDE: Relation.complement,
                NOT: Relation.complement,
            }

        globals_ = Environment(
            name='globals',
            level = self.current_env.level + 1,
            enclosingEnv= self.current_env
        )
        self.current_env = globals_

    def pushCall(self, location, scope):
        """Push a call onto the call stack."""
        Call = namedtuple("Call",['location', 'scope'])
        self.callstack.append(Call(location, scope))

    def popCall(self):
        """Pop a call from the call stack."""
        self.callstack.pop()

    def visit(self, node):
        """Visit an AST Node."""
        try:
            result = super().visit(node)
        except PyrelException as e:
            raise RelationException(self.callstack, node.location, \
                  self.current_env.name, e.msg)
        return result

    def visitModule(self, node):
        self.visitSuite(node)

    def visitSuite(self, node):
        for stmt in node.statements:
            if stmt is not None and stmt != []:
                self.visit(stmt)

    def visitFunctionDefinition(self, node):
        name =  node.name.data()
        parameters = [param.data() for param in node.parameters]
        statements = node.suite
        function = Function(name, parameters, statements)
        self.current_env.define(name, function)

    def visitFunctionCall(self, node):
        function = self.visit(node.callee)
        if not isinstance(function, Callable):
            raise TypeException(self.callstack, node.location, \
                  self.current_env.name,
                "'{}\' object is not callable".format(type(function)))
        self.pushCall(node.location, self.current_env.name)
        resolvedArgs = []
        for arg in node.arguments:
            resolvedArgs.append(self.visit(arg))
        result = function.call(self.callstack, resolvedArgs)
        if type(result) == Environment:

            def eval_function(env, statements):
                env = env
                enclosingEnv = self.current_env
                env.enclosingEnv = enclosingEnv
                env.level = enclosingEnv.level + 1
                self.current_env = env
                r_val = False
                try:
                    self.visitSuite(statements)
                except Return as r:
                    self.current_env = enclosingEnv
                    return r.value

            result = eval_function(result, function.statements)
        self.popCall()
        return result

    def visitReturnStatement(self, node):
        value = self.visit(node.expression) if node.expression else None
        raise Return(value)

    def visitAssignment(self, node):
        target = node.target
        op = node.operator
        expr = node.expression
        if op.tag in (STAREQUAL, AMBEREQUAL, VBAREQUAL): # augmented assignment
            op.tag = op.tag.replace(EQUAL, '')
            expr = BinaryOperation(node.location, target, op, node.expression)
        value = self.visit(expr)
        try:
            value = value.copy() # create a new relation in memory
        except AttributeError:
            pass
        self.current_env.define(target.data(), value)

    def visitImportStatement(self, node):
        module = node.data().data()
        env = self.current_env
        while env.name != "_builtins_":
            env = env.enclosingEnv
        try:
            relathon.import_module(self, env, module)
        except FileNotFoundError:
            raise ModuleNotFoundException(self.callstack, node.location, \
                  self.current_env.name, module)

    def visitWhileStatement(self, node):
        result = self.visit(node.condition)
        if not isinstance(result, Relation) or (result.rows, result.cols) != (1,1):
            raise TypeException(self.callstack, node.location, self.current_env.name, "condition must reduce to a relation of type [1<->1]")
        while result == self.TrueRel:
            try:
                self.visit(node.whileSuite)
            except Continue:
                continue
            except Break:
                break
            result = self.visit(node.condition)

    def visitIfStatement(self, node):
        result = self.visit(node.condition)
        if not isinstance(result, Relation) or (result.rows, result.cols) != (1,1):
            raise TypeException(self.callstack, node.location, self.current_env.name, "condition must reduce to a relation of type [1<->1]")
        if result == self.TrueRel:
            self.visit(node.ifSuite)
        else:
            branched = False
            for elif_ in node.elifStatements:
                if self.visitElifStatement(elif_):
                    branched = True
                    break
            if node.elseSuite and not branched:
                self.visit(node.elseSuite)

    def visitElifStatement(self, node):
        result = self.visit(node.condition)
        if not isinstance(result, Relation) or (result.rows, result.cols) != (1,1):
            raise TypeException(self.callstack, node.location, self.current_env.name, "condition must reduce to a relation of type [1<->1]")
        if result == self.TrueRel:
            self.visit(node.body)
            return True
        else:
            return False

    def visitTernaryOperation(self, node):
        result = self.visit(node.condition)
        if not isinstance(result, Relation) or (result.rows, result.cols) != (1,1):
            raise TypeException(self.callstack, node.location, self.current_env.name, "condition must reduce to a relation of type [1<->1]")

        if result == self.TrueRel:
            value = self.visit(node.expr)
        else:
            value = self.visit(node.orElse)
        return value

    def getRelOperation(self, operator):
        operation = self.operatorToOperation.get(operator, NotImplemented)
        if operation == NotImplemented:
            raise NotImplementedError
        return operation

    def visitBinaryOperation(self, node):
        lhs = self.visit(node.left)
        operator = node.operator
        rhs = self.visit(node.right)
        operation = self.getRelOperation(operator.tag)
        try:
            if type(rhs) != Relation:
                raise AttributeError
            result = operation(lhs, rhs)
        except AttributeError:
            lhs_name = lhs.__class__.__name__
            rhs_name = rhs.__class__.__name__
            if type(lhs) == str:
                lhs_name = 'char'
            if type(rhs) == str:
                rhs_name = 'char'
            raise TypeException(self.callstack, node.location, self.current_env.name, "unsupported operand type for {}: \'{}\' and \'{}\'".format(node.data(), lhs_name, rhs_name))
        else:
            return result

    def visitBooleanOperation(self, node):
        return self.visitBinaryOperation(node)

    def visitComparison(self, node):
        result =  self.visitBinaryOperation(node)
        return self.TrueRel if result else self.FalseRel

    def visitUnaryOperation(self, node):
        operand = self.visit(node.operand)
        operation = self.getRelOperation(node.operator.tag)
        try:
            result = operation(operand)
        except AttributeError:
            raise TypeException(self.callstack, node.location, self.current_env.name, "bad operand type for unary {}: \'{}\'.".format(node.data(), operand.__class__.__name__))
        else:
            return result

    def visitVariable(self, node):
        identifier = node.data()
        value = self.current_env.resolve(identifier)
        if value is False: # Not defined
            raise NameException(self.callstack, node.location, self.current_env.name, identifier)
        return value

    def visitOrderedPairs(self, node):
        class OrderedPairs:

            def __init__(self, pairs):
                self.pairs = pairs

            def __str__(self):
                return "[" + str(self.pairs)[1:-1] + "]"

        pairs = []
        for x,y in node.pairs:
            pair = self.visit(x), self.visit(y)
            pairs.append(pair)
        return OrderedPairs(pairs)

    def visitPassStatement(self, node):
        pass

    def visitContinueStatement(self, node):
        raise Continue

    def visitBreakStatement(self, node):

        raise Break

    def visitInteger(self, node):
        integer = node.data()
        return integer

    def visitFloat(self, node):
        integer = node.data()
        return integer

    def visitBoolean(self, node):
        if node.value == True:
            return self.TrueRel
        else:
            return self.FalseRel

    def visitChar(self, node):
        char = node.data()
        return char

    def visitNone_(self, node):
        return None