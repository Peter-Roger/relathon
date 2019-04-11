# Copyright Peter Roger. All rights reserved.
#
# This file is part of relathon. Use of this source code is governed by
# the GPL license that can be found in the LICENSE file.

"""The Relathon Lexigraphical Analyzer (lexer)."""

import re
import sys
from tok import *
from location import *
from errors import LexerException, IndentationException

TABSIZE = 8

class Lexer:

    EXPRESSIONS = (
        (NEWLINE,r'\n'), # New lines can have preceding whitescape
        (BLANKLINE, r'[ \t]+\n'),
        (ESCAPED_NEWLINE,r'\\(?:\r\n?|\n)'),
        (COMMENT, r'(\s)*#.*'), # Comments end with a newline
        (WHITESPACE, r'[ \t]+'),
        (IDENTIFIER, r'[A-Za-z_][A-Za-z0-9_-]*'), # Valid Pythonic Identifier
        (CHAR, r'\".\"|\'.\''),
        (FLOAT, r'(([1-9]\d*|0)*\.\d+)'),
        (INTEGER, r'([1-9]\d*|0)'),
        (LPAR, r'\('),
        (RPAR, r'\)'),
        (LSQB, r'\['),
        (RSQB, r'\]'),
        (COLON, r'\:'),
        (COMMA, r'\,'),
        (SEMI, r'\;'),
        (STAREQUAL, r'\*='),
        (VBAREQUAL, r'\|='),
        (AMBEREQUAL, r'\&='),
        (EQEQUAL, r'=='),
        (NOTEQUAL, r'!='),
        (LESSEQUAL, r'<='),
        (GREATEREQUAL, r'>='),
        (LESS, r'<'),
        (GREATER, r'>'),
        (STAR, r'\*'),
        (VBAR, r'\|'),
        (AMBER, r'\&'),
        (CIRCUMFLEX, '\^'),
        (EQUAL, r'\='),
        (TILDE, '\~'),
    )

    # refer to named groups in the python regex docs
    named_groups = ['(?P<{}>{})'.format(tag, expr) for tag, expr in EXPRESSIONS]
    REGEX = re.compile('|'.join(named_groups))
    del named_groups

    KEYWORDS = {
        'def': FUNCDEF,
        'import' : IMPORT,
        'return': RETURN,
        'if': IF,
        'elif': ELIF,
        'else': ELSE,
        'while': WHILE,
        'continue': CONTINUE,
        'break': BREAK,
        'pass': PASS,
        'and' : AND,
        'or': OR,
        'not' : NOT,
        'True' : TRUE,
        'False' : FALSE,
        'None' : NONE
    }

    def __init__(self, source, prompt=False):
        self.filename = source.filename
        self.string = source.string
        self.prompt = prompt
        if self.prompt:
            source.string += '\n'

        self.tokens = []
        self.current_token = None
        self.token_index = 0

        self.p = 0
        self.column = 0
        self.line_num = 1 # line count begins at 1
        self.atbol = True # set to True at initialization and after newline token is returned
        self.nesting = 0
        self.blocks = 0

        self.indent = 0
        self.pending_indents = 0
        self.indent_stack = [self.indent]

        if self.prompt:
            self.tokenize()

    def tokenize(self):
        """Tokenizes the entire source in one continuous pass.
        Used during interactive mode.
        """
        tok = self.extractToken()
        self.tokens = [tok]
        while tok.tag != EOF:
            tok = self.extractToken()
            self.tokens.append(tok)

    def nextToken(self):
        """Return the next token.

        Returns:
            token
        """
        if self.prompt:
            if self.token_index < len(self.tokens):
                self.current_token = self.tokens[self.token_index]
                self.token_index += 1
        else:
            self.current_token = self.extractToken()
            self.tokens.append(self.current_token)
        return self.current_token

    def extractToken(self):
        """Matches the next sequence of input from the source with a recognized
        pattern and returns the lexeme as a lexical token.

        Returns:
            Token - the next lexical token

        Raises:
            LexicalError - if the next token is not recogized
        """
        sameLogicalLine = False
        while self.p < len(self.string):
            if not sameLogicalLine: # then lineBegin and columnBegin are new
                loc = Location(self.filename, self.p, self.line_num, self.column, self.line_num, self.column)
            else:
                sameLogicalLine = False

            match = self.REGEX.match(self.string, self.p)
            if not match:
                loc.columnEnd += 1
                raise LexerException(loc)
            else:
                tag = match.lastgroup
                lexeme = match.group(tag)
                self.p = match.end(tag)
                # escaped or nested newline does not constitute a new logical line
                if tag == ESCAPED_NEWLINE or (tag == NEWLINE and self.nesting > 0):
                    self.line_num += 1
                    self.column = 0
                    loc.lineEnd = self.line_num
                    sameLogicalLine = True
                    continue

                # Only Beginning Of Line affects indentation
                if self.atbol:
                    self.atbol = False

                    # blanklines and comment only lines do not affect indentation
                    if tag in (BLANKLINE, COMMENT, NEWLINE):
                        if tag == NEWLINE and self.prompt:
                            if self.blocks:
                                self.blocks = 0
                            continue
                        else:
                            self.atbol = True
                            self.line_num += 1
                        continue

                    if tag == WHITESPACE:
                        num_of_tabs = lexeme.count('\t')
                        self.column = num_of_tabs * TABSIZE + (len(lexeme) - num_of_tabs)
                        loc.columnEnd = self.column
                    if self.column > self.indent_stack[self.indent]:
                        self.indent_stack.append(self.column)
                        self.indent += 1
                        self.pending_indents += 1
                    elif self.column < self.indent_stack[self.indent]:
                        while self.indent > 0 and self.column < self.indent_stack[self.indent]:
                            self.indent -= 1
                            self.pending_indents -= 1
                        if self.column != self.indent_stack[self.indent]:
                            beg = self.p - self.column
                            raise IndentationException(loc, lexer=True)
                    else: # no change of indentation
                        if tag == WHITESPACE:
                            continue

                    # Return pending indentation
                    if self.pending_indents != 0:
                        if self.pending_indents < 0:
                            self.pending_indents += 1
                            self.p = match.start() # DEDENT is not a character with a length, so don't count it
                            return Token(DEDENT, DEDENT, loc)
                        else:
                            self.pending_indents -= 1
                            return Token(INDENT, INDENT, loc)

                elif tag == WHITESPACE: # skip all other whitespace (e.g. nested whitespace)
                    self.column += len(lexeme)
                    continue

                if tag in (COMMENT, NEWLINE, BLANKLINE):
                    # loc.lineEnd += 1
                    loc.columnEnd = 0
                    if tag in (NEWLINE, BLANKLINE):
                        if self.blocks:
                            self.blocks = 1
                        self.atbol = True
                        self.line_num += len(lexeme)
                        self.column = 0
                        return Token(NEWLINE, "\n", loc)
                    self.line_num += 1
                    continue # skip comments

                if tag in (LPAR, LSQB):
                    self.nesting += 1

                elif tag in (RPAR, RSQB):
                    self.nesting -= 1

                if tag == COLON:
                    self.blocks = 1

                length = len(lexeme)
                if tag == IDENTIFIER:
                    if lexeme in self.KEYWORDS:
                        tag = self.KEYWORDS[lexeme]
                loc.columnEnd += length
                self.column += length
                token = Token(tag, lexeme, loc)
                return token

        loc = Location(self.filename, self.p-1, self.line_num, self.column-1, self.line_num, self.column-1)
        tok = Token(EOF, None, loc)
        return tok