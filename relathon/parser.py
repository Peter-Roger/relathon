# Copyright Peter Roger. All rights reserved.
#
# This file is part of relathon. Use of this source code is governed by
# the GPL license that can be found in the LICENSE file.

"""A recursive decent parser with a lookahead of 2.

Each function corresponds to a production rule in the grammar. The
grammar should be considered documentation for this module and can
be found in grammar.txt.
"""

from tok import *
from lexer import Lexer
import ast_node as ast
from location import Location, NoLoc
from errors import ParserException, IndentationException


ASSIGN_OP = (EQUAL, STAREQUAL, VBAREQUAL, AMBEREQUAL)
BOOL_OP = (OR, AND)
COMP_OP = (LESS, GREATER, EQEQUAL, LESSEQUAL, GREATEREQUAL, NOTEQUAL)
FLOW = (BREAK, CONTINUE, PASS)
BOOL = (TRUE, FALSE)
LITERAL = (*BOOL, INTEGER, FLOAT, CHAR, NONE)

class Incomplete(Exception):
    pass

class Parser:

    k = 2

    def __init__(self, lexer):
        self.lexer = lexer
        self.prompt = lexer.prompt

        self.lookahead = [None] * self.k
        self.p = 0
        self.prevTok = None
        # initialize self.lookahead
        self._consume()
        self._consume()
        self.location = Location(self.lexer.filename, self.p, 1, 0, 1, 0)

        self.inLoop = False

    def _consume(self):
        self.location = getattr(self.lookahead[self.p], "location", NoLoc)
        self.prevTok = self.lookahead[self.p]
        self.lookahead[self.p] = self.lexer.nextToken()
        self.p = (self.p+1) % self.k

    def _error(self, expected=None, arg=None):
        tok = self._lookaheadToken(1)
        if tok.tag == EOF:
            msg = "unexpected EOF while parsing"
        elif tok.tag in (BREAK, CONTINUE):
            msg = "\'{}\' not properly in loop.".format(tok.lexeme)
            raise ParserException(tok.location, msg, tok.tag)
        elif tok.tag in ASSIGN_OP:
            msg = "Can't assign to {}".format(arg.__class__.__name__)
        else:
            msg = "invalid syntax"
        if tok.tag == INDENT or expected == INDENT:
            isExpected = True if expected == INDENT else False
            raise IndentationException(tok.location, expected=isExpected)
        if expected:
            if type(expected) in (list, tuple):
                expected = " or ".join(expected)
            msg += ", expected {} but found \"{}\"".format(expected, tok.lexeme)
        raise ParserException(tok.location, msg, tok.tag)

    def _match(self, *token_types):
        if (self._lookahead(1) in token_types):
            self._consume()
        else:
            self._error(expected=token_types)

    def _lookaheadToken(self, i):
        return self.lookahead[(self.p+i-1)%self.k]

    def _lookahead(self, i):
        return self._lookaheadToken(i).tag

    def _location(self, begin):
        return begin.combine(self.location)

    def parse(self, parseMethod):
        try:
            return parseMethod(self)
        except Incomplete:
            return None

    def nearEnd(self):
        return all(t.tag in (DEDENT, NEWLINE, EOF) for t in self.lookahead[self.p:])

    def module(self):
        # (NEWLINE | stmt)* ENDMARKER
        beginloc = self.location
        stmts = []
        if self._lookaheadToken(1):
            while self._lookahead(1) != EOF:
                if self._lookahead(1)  == NEWLINE:
                    self._match(NEWLINE, INDENT)
                    continue
                else:
                    stmts.append(self.statement())
        return ast.Module(self._location(beginloc), stmts)

    def single_input(self):
        # single_input: NEWLINE | simple_stmt | compound_stmt NEWLINE
        if self._lookahead(1) in (NEWLINE, INDENT, EOF):
            self._match(NEWLINE, EOF)
            return self.null()
        elif self._lookahead(1) in (IF, WHILE, FUNCDEF):
            stmt = self.compound_stmt()
        else:
            stmt = self.simple_stmt()
        return stmt

    def statement(self):
        beginloc = self.location
        if self._lookahead(1) in (IF, WHILE, FUNCDEF):
            stmt = self.compound_stmt()
        else:
            stmt = self.simple_stmt() # could be a list of statements
        return stmt

    def compound_stmt(self):
        beginloc = self.location
        if self._lookahead(1) == IF:
            compound = self.if_stmt()
        elif self._lookahead(1) == WHILE:
            compound = self.while_stmt()
        else:
            compound = self.functionDef()
        return compound

    def simple_stmt(self):
        beginloc = self.location
        small_stmt = self.small_stmt()
        while self._lookahead(1) == SEMI and self._lookahead(2) != NEWLINE:
            small_stmt = [small_stmt]
            self._match(SEMI)
            small = self.small_stmt()
            small_stmt.append(small)
        if self._lookahead(1) == SEMI:
            self._match(SEMI)
        if self._lookahead(1) == EOF:
            self._match(EOF)
        else:
            self._match(NEWLINE)
        if type(small_stmt) == list:
            small_stmt = ast.Suite(self._location(beginloc), small_stmt)
        return small_stmt

    def small_stmt(self):
        beginloc = self.location
        if self._lookahead(1) in FLOW:
            stmt = self.control_stmt()
        elif self._lookahead(1) == RETURN:
            self._match(RETURN)
            if self._lookahead(1) in (NEWLINE, EOF): # Return None
                expr = None
            else:
                expr = self.expr()
            stmt = ast.ReturnStatement(self._location(beginloc), expr)
        elif self._lookahead(1) == IMPORT:
            stmt = self.import_stmt()
        else:
            stmt = self.expr_stmt()
        return stmt

    def expr_stmt(self):
        beginloc = self.location
        expr_stmt = self.expr()
        if self._lookahead(1) in ASSIGN_OP:
            if type(expr_stmt) != ast.Variable:
                self._error(arg=expr_stmt)
            op = self._lookaheadToken(1)
            self._match(*ASSIGN_OP)
            expr = self.expr()
            expr_stmt = ast.Assignment(self._location(beginloc), expr_stmt, op, expr)
        return expr_stmt

    def control_stmt(self):
        beginloc = self.location
        if self._lookahead(1) == BREAK:
            if self.inLoop:
                self._match(BREAK)
                stmt = ast.BreakStatement(self._location(beginloc))
            else:
                self._error()
        elif self._lookahead(1) == CONTINUE:
            if self.inLoop:
                self._match(CONTINUE)
                stmt = ast.ContinueStatement(self._location(beginloc))
            else:
                self._error()
        else:
            self._match(PASS)
            stmt = ast.PassStatement(self._location(beginloc))
        return stmt

    def functionDef(self):
        beginloc = self.location
        self._match(FUNCDEF)
        identifier = self.name()
        parameters = self.paramlist()
        if self._lookahead(1) == COLON:
            self._match(COLON)
            body = self.suite()
        elif self._lookahead(1) == EQUAL: # Single Line function
            self._match(EQUAL)
            expr = self.expr()
            body = ast.Suite(self._location(beginloc), [ast.ReturnStatement(self._location(beginloc), expr)])
        else:
            self._error([COLON, EQUAL])
        return ast.FunctionDefinition(self._location(beginloc), identifier, parameters, body)

    def paramlist(self):
        parameters = []
        self._match(LPAR)
        while self._lookahead(1) != RPAR:
            parameters.append(self.param())
            if self._lookahead(1) == COMMA:
                self._match(COMMA)
        self._match(RPAR)
        return parameters

    def param(self):
        name = self.name()
        return ast.Parameter(name.location, name)

    def suite(self):
        beginloc = self.location
        stmts = []
        if self._lookahead(1) == NEWLINE:
            self._match(NEWLINE)
            if self._lookahead(1) == INDENT:
                self._match(INDENT)
                stmt = self.statement()
                stmts.extend(stmt if type(stmt) == list else [stmt])
                while self._lookahead(1) not in (DEDENT, EOF):
                    stmt = self.statement()
                    stmts.extend(stmt if type(stmt) == list else [stmt])
                if self._lookahead(1) == DEDENT:
                    self._match(DEDENT)
        if not stmts: # this should raise an indentation error
            self._error(INDENT)
        return ast.Suite(self._location(beginloc), stmts)

    def import_stmt(self):
        beginloc = self.location
        self._match(IMPORT)
        module = self.name()
        return ast.ImportStatement(self._location(beginloc), module)

    def if_stmt(self):
        beginloc = self.location
        self._match(IF)
        condition = self.expr()
        self._match(COLON)
        suite = self.suite()
        elif_stmts = []
        else_stmt = []
        while self._lookahead(1) == ELIF:
            self._match(ELIF)
            elif_condition = self.expr()
            self._match(COLON)
            body = self.suite()
            _elif = ast.ElifStatement(self._location(beginloc), elif_condition, body)
            elif_stmts.append(_elif)
        if self._lookahead(1) == ELSE:
            self._match(ELSE)
            self._match(COLON)
            else_stmt = self.suite()
        return ast.IfStatement(self._location(beginloc), condition, suite, elif_stmts, else_stmt)

    def while_stmt(self):
        beginloc = self.location
        self._match(WHILE)
        condition = self.expr()
        self._match(COLON)
        self.inLoop = True
        suite = self.suite()
        self.inLoop = False
        _else = None
        if self._lookahead(1) == ELSE:
            self._match(ELSE)
            self._match(COLON)
            _else = self.suite()
        return ast.WhileStatement(self._location(beginloc), condition, suite, _else)

    def expr(self):
        beginloc = self.location
        expr = self.or_expr()
        if self._lookahead(1) == IF:
            self._match(IF)
            condition = self.expr()
            self._match(ELSE)
            orelse = self.expr()
            return ast.TernaryOperation(self._location(beginloc), expr, condition, orelse)
        return expr

    def or_expr(self):
        beginloc = self.location
        expr = self.and_expr()
        if self._lookahead(1) == OR:
            op = self._lookaheadToken(1)
            self._match(OR)
            right_expr = self.or_expr()
            expr = ast.BooleanOperation(self._location(beginloc), expr, op, right_expr)
        return expr

    def and_expr(self):
        beginloc = self.location
        expr = self.not_expr()
        if self._lookahead(1) == AND:
            op = self._lookaheadToken(1)
            self._match(AND)
            right_expr = self.and_expr()
            expr = ast.BooleanOperation(self._location(beginloc), expr, op, right_expr)
        return expr

    def not_expr(self):
        beginloc = self.location
        if self._lookahead(1) == NOT:
            op = self._lookaheadToken(1)
            self._match(NOT)
            operand = self.not_expr()
            expr = ast.UnaryOperation(self._location(beginloc), operand, op)
        else:
            expr = self.comparison()
        return expr

    def comparison(self):
        beginloc = self.location
        left = self.factor()
        if self._lookahead(1) in COMP_OP:
            op = self._lookaheadToken(1)
            self._match(*COMP_OP)
            right = self.comparison()
            return ast.Comparison(self._location(beginloc), left, op, right)
        return left

    def factor(self):
        beginloc = self.location
        factor = self.term()
        if self._lookahead(1) in (VBAR, AMBER):
            op = self._lookaheadToken(1)
            self._match(VBAR, AMBER)
            right_factor = self.factor()
            factor = ast.BinaryOperation(self._location(beginloc), factor, op, right_factor)
        return factor

    def term(self):
        beginloc = self.location
        term = self.unary_term()
        if self._lookahead(1) == STAR:
            op = self._lookaheadToken(1)
            self._match(STAR)
            right_term = self.term()
            term = ast.BinaryOperation(self._location(beginloc), term, op, right_term)
        return term

    def unary_term(self):
        beginloc = self.location
        if self._lookahead(1) == TILDE:
            op = self._lookaheadToken(1)
            self._match(TILDE)
            operand = self.unary_term()
            term = ast.UnaryOperation(self._location(beginloc), operand, op)
        else:
            term = self.atom_expr()
            while self._lookahead(1) == CIRCUMFLEX:
                op = self._lookaheadToken(1)
                self._match(CIRCUMFLEX)
                term = ast.UnaryOperation(self._location(beginloc), term, op)
        return term

    def atom_expr(self):
        beginloc = self.location
        atom = self.atom()
        if self._lookahead(1) == LPAR:
            trailer = self.trailer()
            return ast.FunctionCall(self._location(beginloc), atom, trailer)
        return atom

    def trailer(self):
        self._match(LPAR)
        arglist = self.arglist()
        self._match(RPAR)
        return arglist

    def arglist(self):
        if self._lookahead(1) == RPAR:
            args = []
        else:
            args = [self.expr()]
            while self._lookahead(1) == COMMA and self._lookahead(2) != RPAR:
                self._match(COMMA)
                args.append(self.expr())
        if self._lookahead(1) == COMMA:
            self._match(COMMA)
        return args

    def atom(self):
        la1 = self._lookahead(1)
        if la1 == IDENTIFIER:
            atom = self.name()
        elif la1 in LITERAL:
            atom = self.literal()
        elif la1 == LPAR:
            self._match(LPAR)
            atom = self.expr()
            self._match(RPAR)
        elif la1 == LSQB:
            atom = self.ordered_pairs()
        else:
            self._error()
        return atom

    def name(self):
        beginloc = self.location
        identifier = self._lookaheadToken(1)
        self._match(IDENTIFIER)
        return ast.Variable(self._location(beginloc), identifier)

    def literal(self):
        beginloc = self.location
        la1 = self._lookahead(1)
        if la1 == INTEGER:
            literal = self.integer()
        elif la1 == FLOAT:
            literal = self.float()
        elif la1 in BOOL:
            literal = self.boolean()
        elif la1 == CHAR:
            literal = self.char()
        elif la1 == NONE:
            literal = self.none()
        else:
            self._error()
        return literal

    def ordered_pairs(self):
        beginloc = self.location
        self._match(LSQB)
        pairs = []
        if self._lookahead(1) != RSQB:
            pairs.append(self.pair())
            while self._lookahead(1) == COMMA and self._lookahead(2) != RSQB:
                self._match(COMMA)
                pairs.append(self.pair())
            if self._lookahead(1) == COMMA:
                self._match(COMMA)
        self._match(RSQB)
        return ast.OrderedPairs(self._location(beginloc), pairs)

    def pair(self):
        self._match(LPAR)
        element_x = self.integer()
        self._match(COMMA)
        element_y = self.integer()
        self._match(RPAR)
        return element_x, element_y

    def integer(self):
        beginloc = self.location
        integer = self._lookaheadToken(1)
        self._match(INTEGER)
        return ast.Integer(self._location(beginloc), integer)

    def float(self):
        beginloc = self.location
        float_ = self._lookaheadToken(1)
        self._match(FLOAT)
        return ast.Float(self._location(beginloc), float_)

    def boolean(self):
        beginloc = self.location
        _bool = self._lookaheadToken(1)
        self._match(*BOOL)
        return ast.Boolean(self._location(beginloc), _bool)

    def char(self):
        beginloc = self.location
        char = self._lookaheadToken(1)
        self._match(CHAR)
        return ast.Char(self._location(beginloc), char)

    def none(self):
        beginloc = self.location
        self._match(NONE)
        return ast.None_(self._location(beginloc))

    def null(self):
        return ast.Null(self.location)