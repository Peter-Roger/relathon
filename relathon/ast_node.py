# Copyright Peter Roger. All rights reserved.
#
# This file is part of relathon. Use of this source code is governed by
# the GPL license that can be found in the LICENSE file.

"""This module provides a class for each node type of the abstract
syntax tree (ast). The parser builds the ast. The structure of the tree and
the type of each node encodes semantic meaning that the interpreter can
then evaluate."""

from abc import ABC

class ASTNode:
    """Abstract class for a node of an irregular heterogeneous abstract syntax tree.
    """
    def __init__(self, location):
        self.location = location

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                all(val == other.__dict__[key] for key, val in self.__dict__.items()
                    if key != "location"))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "{}({})".format(self.tag(), self.data())

    def data(self):
        return ""

    def tag(self):
        return self.__class__.__name__


class Module(ASTNode):

    def __init__(self, location, statements):
        super().__init__(location)
        self.statements = statements

    def children(self):
        return self.statements

    def data(self):
        return "\"{}\"".format(self.location.filename)


class Suite(ASTNode):

    def __init__(self, location, statements):
        super().__init__(location)
        self.statements = statements

    def children(self):
        return self.statements

    def __iter__(self):
        return iter(self.statements)


class ImportStatement(ASTNode):

    def __init__(self, location, name):
        super().__init__(location)
        self.name = name

    def data(self):
        return self.name


class FunctionDefinition(ASTNode):

    def __init__(self, location, name, parameters, suite):
        super().__init__(location)
        self.name = name
        self.parameters = parameters
        self.suite = suite

    def data(self):
        return [self.name, self.parameters, self.suite]


class Parameter(ASTNode):

    def __init__(self, location, variable):
        super().__init__(location)
        self.variable = variable

    def data(self):
        return self.variable.data()

    def __repr__(self):
        return self.data()

    __str__ = __repr__


class Statement(ASTNode):
    """ABSTRACT"""
    def __init__(self, location):
        super().__init__(location)


class ReturnStatement(Statement):

    def __init__(self, location, expression):
        super().__init__(location)
        self.expression = expression

    def data(self):
        return self.expression


class Assignment(Statement):

    def __init__(self, location, target, operator, expression):
        super().__init__(location)
        self.target = target
        self.operator = operator
        self.expression = expression

    def data(self):
        return self.operator.lexeme


class WhileStatement(Statement):

    def __init__(self, location, condition, whileSuite, _else):
        super().__init__(location)
        self.condition = condition
        self.whileSuite = whileSuite
        self._else = _else


class IfStatement(Statement):

    def __init__(self, location, condition, ifSuite, elifStatements, elseSuite):
        super().__init__(location)
        self.condition = condition
        self.ifSuite = ifSuite
        self.elifStatements = elifStatements
        self.elseSuite = elseSuite


class ElifStatement(Statement):

    def __init__(self, location, condition, body):
        super().__init__(location)
        self.condition = condition
        self.body = body


class BreakStatement(Statement):

    def __init__(self, location):
        super().__init__(location)


class ContinueStatement(Statement):

    def __init__(self, location):
        super().__init__(location)


class PassStatement(Statement):
    def __init__(self, location):
        super().__init__(location)


class Expression(ASTNode):
    """ABSTRACT"""
    def __init__(self, location):
        super().__init__(location)


class TernaryOperation(Expression):

    def __init__(self, location, expr, condition, orElse):
        super().__init__(location)
        self.expr = expr
        self.condition = condition
        self.orElse = orElse

    def data(self):
        return [self.expr, self.condition, self.orElse]


class BinaryOperation(Expression):

    def __init__(self, location, left, operator, right):
        super().__init__(location)
        self.left = left
        self.operator = operator
        self.right = right

    def data(self):
        return self.operator.lexeme


class BooleanOperation(BinaryOperation):

    def __init__(self, location, left, operator, right):
        super().__init__(location, left, operator, right)

    def data(self):
        return [self.left, self.right]


class Comparison(BinaryOperation):

    def __init__(self, location, left, operator, right):
        super().__init__(location, left, operator, right)


class UnaryOperation(Expression):

    def __init__(self, location, operand, operator):
        super().__init__(location)
        self.operand = operand
        self.operator = operator

    def data(self):
        return self.operator.lexeme


class FunctionCall(Expression):

    def __init__(self, location, callee, arguments):
        super().__init__(location)
        self.callee = callee
        self.arguments = arguments

    def data(self):
        return self.callee.data()


class Variable(Expression):

    def __init__(self, location, identifier):
        super().__init__(location)
        self.identifier = identifier

    def data(self):
        return self.identifier.lexeme


class OrderedPairs(Expression):

    def __init__(self, location, pairs):
            super().__init__(location)
            self.pairs = pairs

    def data(self):
        return self.pairs

    def __str__(self):
        return "[" + str(self.pairs)[1:-1] + "]"


class Literal(Expression):

    def __init__(self, location, value):
        super().__init__(location)
        self.value = value

    def data(self):
        return self.value

    def __str__(self):
        return str(self.value)


class Integer(Literal):

    def __init__(self, location, integer):
        super().__init__(location, int(integer.lexeme))


class Float(Literal):

    def __init__(self, location, float_):
        super().__init__(location, float(float_.lexeme))


class Boolean(Literal):

    def __init__(self, location, boolean):
        super().__init__(location, True if boolean.lexeme == 'True' else False)


class Char(Literal):

    def __init__(self, location, char):
        super().__init__(location, str(char.lexeme))


class None_(Literal):

    def __init__(self, location):
        super().__init__(location, None)


class Null(ASTNode):

    def __init__(self, location):
        super().__init__(location)