# Copyright Peter Roger. All rights reserved.
#
# This file is part of relathon. Use of this source code is governed by
# the GPL license that can be found in the LICENSE file.

"""This module contains all of the lexigraphical token types of Relathon."""


EOF             = "EOF"
IDENTIFIER      = "IDENTIFIER"
CHAR            = "CHAR"
INTEGER         = "INTEGER"
FLOAT           = "FLOAT"
NEWLINE         = "NEWLINE"
INDENT          = "INDENT"
DEDENT          = "DEDENT"
LPAR            = "LPAR"
RPAR            = "RPAR"
LSQB            = "LSQB"
RSQB            = "RSQB"
COLON           = "COLON"
COMMA           = "COMMA"
SEMI            = "SEMI"
STAR            = "STAR"
VBAR            = "VBAR"
AMBER           = "AMBER"
CIRCUMFLEX      = "CIRCUMFLEX"
EQEQUAL         = "EQEQUAL"
NOTEQUAL        = "NOTEQUAL"
LESSEQUAL       = "LESSEQUAL"
GREATEREQUAL    = "GREATEREQUAL"
LESS            = "LESS"
GREATER         = "GREATER"
EQUAL           = "EQUAL"
STAREQUAL       = "STAREQUAL"
VBAREQUAL       = "VBAREQUAL"
AMBEREQUAL      = "AMBEREQUAL"
TILDE           = "TILDE"
#keywords
FUNCDEF         = "FUNCDEF"
IMPORT          = "IMPORT"
RETURN          = "RETURN"
IF              = "IF"
ELIF            = "ELIF"
ELSE            = "ELSE"
WHILE           = "WHILE"
CONTINUE        = "CONTINUE"
BREAK           = "BREAK"
PASS            = "PASS"
AND             = "AND"
OR              = "OR"
NOT             = "NOT"
TRUE            = "TRUE"
FALSE           = "FALSE"
NONE            = "NONE"
# these are never passed to the parser
BLANKLINE       = "BLANKLINE"
ESCAPED_NEWLINE = "ESCAPED_NEWLINE"
WHITESPACE      = "WHITESPACE"
COMMENT         = "COMMENT"

class Token(object):
    """Lexigraphical token object."""

    def __init__(self, tag, lexeme, location):
        self.tag = tag
        self.lexeme = lexeme
        self.location = location

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                all(val == other.__dict__[key] for key, val in self.__dict__.items()
                    if key != "location"))

    def __str__(self):
        return "Token({}, {})".format(self.tag, repr(self.lexeme))

    def __repr__(self):
        return self.__str__()