# Copyright Peter Roger. All rights reserved.
#
# This file is part of relathon. Use of this source code is governed by
# the GPL license that can be found in the LICENSE file.

"""This module provides every type of exception that might be produced
during lexing, parsing, or interpreting. Error messages are inspired by
python style error messages.

Exceptions:
    RelathonException
    InterpreterException
    LexerException
    IndentationException
    ParserException
    RelationException
    ArityException
    NameException
    TypeException
    ModuleNotFoundException
"""

__all__ = ['RelathonException', 'InterpreterException', 'LexerException',
           'IndentationException', 'ParserException', 'RelationException',
           'ArityException', 'NameException', 'TypeException',
           'ModuleNotFoundException']

TABSIZE = 8 # also used by lexer; should move into shared globals

class RelathonException(Exception):
    """Exception for errors that arise from Relathon."""
    def __init__(self, location, msg):
        self.location = location
        self.msg = msg

    def __str__(self):
        return self.msg

    def get_message(self, string, prompt=False):
        if issubclass(self.__class__, InterpreterException):
            err_msg = self.get_trace_back_msg(string, prompt)
        elif isinstance(self, (LexerException, ParserException, IndentationException)):
            err_msg = self._get_invalid_syntax_msg(string)
        else:
            raise NotImplementedError
        sep = '\n' if err_msg else ''
        err_msg = err_msg if err_msg else ''
        return "{}{}{}Error: {}".format(err_msg, sep, self.TYPE, self.msg.rstrip())

    @classmethod
    def _get_line(cls, location, string):
        """Get the full line of where the error occurred."""
        i = location.pos
        j = i + 1
        beg = False if i != 0 else True
        end = False if j < len(string) else True
        # bidirectional linear search from the point of error to find
        # beginning and end of source line
        while not beg or not end:
            if not beg:
                if i > 0 and string[i] != '\n':
                    i -= 1
                else:
                    beg = True
            if not end:
                if j < len(string) and string[j] != '\n':
                    j += 1
                else:
                    end = True
        line = string[i:j]
        return line.strip()

    def _fmt_location(self, location, scope=None):
        """Formats location of error into a readable string."""
        fmt_loc = "  File \"{fname}\", line {lineno}{scope}".format(
            fname=location.filename,
            lineno=location.lineBegin,
            scope= ", in " + scope if scope else "")
        return fmt_loc

    def _get_invalid_syntax_msg(self, string):
        """Formats string for syntax errors."""
        location = self._fmt_location(self.location)
        line = self._get_line(self.location, string)
        num_of_tabs = line.count('\t')
        whitespace = (len(line) - len(line.strip())) + num_of_tabs * (TABSIZE - 1)
        position = self.location.columnBegin - whitespace
        carrot = "{space}^".format(space=position * " ")
        return "{loc}\n    {line}\n    {car}".format(loc=location, line=line.strip(), car=carrot)


class LexerException(RelathonException):
    """Exception for errors that occur in the Lexer."""
    TYPE = "Lexical"

    def __init__(self, location):
        msg = "Invalid character"
        super().__init__(location, msg)


class ParserException(RelathonException):
    """Exception for errors that occur in the Parser."""
    TYPE = "Syntax"

    def __init__(self, location, msg=None, tag=None):
        self.tag = tag
        if not msg:
            msg = "Invalid Syntax."
        super().__init__(location, msg)


class InterpreterException(RelathonException):
    """Exception for all Relathon runtime errors that occur during
    interpretation or evalution

    Attributes:
    callstack - the current call stack when the error occurred
    """
    TYPE = "Runtime"

    def __init__(self, callstack, location, scope, msg):
        super().__init__(location, msg)
        self.callstack = callstack
        self.scope = scope

    def get_trace_back_msg(self, string, prompt=False):
        """Goes through call stack to build traceback message and
        returns it.

        Args:
            string - source code
            prompt - True if in interactive mode

        Returns:
            the trace back error message
        """
        trace = []
        prevLineBeging = -1
        for call in self.callstack:
            if call.location.lineBegin != prevLineBeging:
                loc = self._fmt_location(call.location, call.scope)
                if not prompt:
                    line = "    " + self._get_line(call.location, string).strip()
                    trace.extend([loc, line])
                else:
                    trace.append(loc)
            prevLineBeging = call.location.lineBegin

        self.callstack.clear()
        if self.location.lineBegin != prevLineBeging:
            loc = self._fmt_location(self.location, self.scope)
            if not prompt:
                line = "    " + self._get_line(self.location, string).strip()
                trace.extend([loc, line])
            else:
                trace.append(loc)
        return "{}{}".format("Traceback (most recent call last):\n" if len(self.callstack) else "",'\n'.join(trace))

class ModuleNotFoundException(InterpreterException):
    """Exception when importing a module that can't be found."""

    TYPE = "ModuleNotFound"

    def __init__(self, callstack, location, scope, module_name):
        msg = "No module named \'{}\'".format(module_name)
        super().__init__(callstack, location, scope, msg)

class ArityException(InterpreterException):
    """Exception for when the arguments to a function call do not match
    the parameters to the function definition.

    Attributes:
        callee (str) - name of called function
        arity (2-tuple) - range of number of parameters
        params (list) - the parameters
    """

    TYPE = "Arity"

    def __init__(self, callstack, callee, arity, parameters, arguments):
        self.callee = callee
        self.arity = arity
        self.params = parameters
        super().__init__(callstack, callstack[-1].location, self.callee, self.getArityMessage(len(arguments)))

    def getArityMessage(self, argc):
        """Generates useful arity related error messages."""
        arities = range(*self.arity)
        if argc > arities.stop:
            string = "{callee}() takes {arity_s} positional arguments " \
                "but {argc} were given".format(
                    callee = self.callee,
                    arity_s = str(arities.start) if arities.start == arities.stop else
                     "from {} to {}".format(str(arities.start), str(arities.stop)),
                    argc = argc
                )
        else:
            start = arities.start
            params = self.params
            difference = start - argc
            string = "{callee}() missing {diff} required positional " \
                "argument{plural}: {params}".format(
                    callee=self.callee,
                    diff=difference,
                    plural="s" if difference > 1 else "",
                    params="{}{}{}{}.".format(
                        ", ".join("\'{}\'".format(str(p)) for p in params[argc:start-1]),
                            "," if len(params[argc:start]) > 2 else "",
                        " and " if len(params[argc:start]) > 1 else "",
                        "\'{}\'".format(params[argc:start][-1] if len(params[argc:start]) > 0 else '')
                    )
                )
        return string


    def __str__(self):
        return self._getMessage()


class RelationException(InterpreterException):
    """Exceptions for errors that occur from bad or invalid operations
    on relations."""
    TYPE = "Relation"

    def __init__(self, callstack, location, scope, msg):
        self.msg = msg
        super().__init__(callstack, location, scope, msg)


class NameException(InterpreterException):
    """Exception for errors that result from a failed name resolution."""

    TYPE = "Name"

    def __init__(self, callstack, location, scope, name):
        msg = "name \'{}\' is not defined".format(name)
        super().__init__(callstack, location, scope, msg)


class TypeException(InterpreterException):
    """Exception for errors that occur in the Type Checker."""
    TYPE = "Type"

    def __init__(self, callstack, location, scope, msg):
        super().__init__(callstack, location, scope, msg)

class IndentationException(RelathonException):
    """Indentation Error."""
    TYPE = "Indentation"

    def __init__(self, location, lexer=False, expected=False):
        self.lexer = lexer
        self.expected = expected
        if self.lexer:
            msg = "unindent does not match any outer indentation level"
        else:
            if self.expected:
                msg = "expected an indented block"
            else:
                msg = "unexpected indent"
        super().__init__(location, msg)