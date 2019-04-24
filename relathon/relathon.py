# Copyright Peter Roger. All rights reserved.
#
# This file is part of relathon. Use of this source code is governed by
# the GPL license that can be found in the LICENSE file.

"""This module is the interface to the Relathon programming language.
To execute relathon scripts simply run this module and pass the name
of the script (.rel extension) as an argument. To enter into interactive
console mode run this module and omit any arguments.

Classes:
    Source - Relathon module source code
    Relathon - Interface to the Relathon programming language. Executes
        relathon scripts and provides an interactive shell that closely emulates the python shell.
"""
import sys, code
from ast_node import Expression, Null
from lexer import Lexer
from parser import Parser
import interpreter
from errors import IndentationException, LexerException, ParserException, RelathonException
from pyrel import PyrelException

VERSION = '0.1.1'

class Source:
    """Relathon source code.

    Attributes:
        filename (str) - name of source file object
        string (str) - the source code string
    """

    def __init__(self, filename, string=None):
        self.filename = filename
        self.string = string
        if string == None:
            self.read()

    def read(self):
        with open(self.filename) as (f):
            self.string = f.read()

    def __str__(self):
        return 'Filename: {}\n{}'.format(self.filename, self.string)

    __repr__ = __str__


class Relathon:
    """Interface to the Relathon Interpreter. Runs relathon scripts or interprets in an interactive console mode.

    Attributes:
        ps1 - prompt string
        ps2 - secondary prompt string
        banner - Console banner
    """
    ps1 = '>>> '
    ps2 = '... '
    banner = ('Relathon {v}').format(v=VERSION)

    @classmethod
    def run(cls, fd, intrpr=None):
        """Parse and run source from a file."""
        source = Source(fd.name, fd.read())
        ast = cls.parse(source)
        if not intrpr:
            intrpr = interpreter.Interpreter()
        intrpr.visit(ast)
        return intrpr

    @classmethod
    def parse(cls, source, prompt=False):
        """Parse source and return the abstract syntax tree.

        Returns:
            if more input is needed, returns None, otherwise returns
            the abstract syntax tree of the source.

        Raises:
            LexerException - Lexigraphical Errors
            ParserException - Grammatical Errors
        """
        lexer = Lexer(source, prompt=prompt)
        parser = Parser(lexer)
        parseMethod = Parser.module
        if prompt == True:
            parseMethod = Parser.single_input
            if lexer.nesting > 0 or lexer.blocks > 0:
                try:
                    parser.parse(parseMethod)
                except IndentationException as e:
                    if not (e.lexer or e.expected):
                        raise e
                except ParserException as e:
                    if e.tag in ('EOF', 'NEWLINE'):
                        pass
                    else:
                        raise e
                return
        return parser.parse(parseMethod)

    @classmethod
    def interact(cls, locals=None):
        class RelathonConsole(code.InteractiveConsole):
            """Closely emulate the behavior of the interactive Python interpreter."""

            def __init__(self, filename=None):
                self.interpreter = interpreter.Interpreter()
                super().__init__(filename=filename)

            def runsource(self, source, filename=None, symbol=None):
                try:
                    source += '\n'
                    ast = cls.parse(Source(filename, source), prompt=True)
                except (LexerException, ParserException, IndentationException) as e:
                    cls.print_error(e, source, prompt=True)
                    return False

                if ast is None:
                    return True
                if not isinstance(ast, Null):
                    try:
                        result = self.interpreter.visit(ast)
                    except RelathonException as e:
                        try:
                            cls.print_error(e, source, prompt=True)
                        finally:
                            e = None
                            del e

                    else:
                        if result and issubclass(type(ast), Expression):
                            print(result)
                        return False

        try:
            import readline
        except ImportError:
            pass

        ps1, ps2 = getattr(sys, 'ps1', None), getattr(sys, 'ps2', None)
        try:
            sys.ps1, sys.ps2 = cls.ps1, cls.ps2
            (RelathonConsole(filename='<stdin>')).interact(banner=cls.banner, exitmsg='')
        finally:
            sys.ps1, sys.ps2 = ps1, ps2

    @classmethod
    def run_in_main(cls, fd=None, interact=False, imprt=False, intrpr=None):
        """Read source from input and run source."""
        if fd is None:
            fd = sys.stdin
        else:
            try:
                suffix = '.rel' if imprt else ''
                fd = open('{}{}'.format(fd, suffix))
            except FileNotFoundError as e:
                if imprt:
                    raise FileNotFoundError
                else:
                    print(("Relathon can't open file '{fname}': {reason}").format(fname=fd,
                      reason=str(e)))
                exit_code = 1
                return exit_code

        if fd.isatty():
            cls.interact()
            exit_code = 1
        else:
            try:
                exit_code = 0
                intrpr = cls.run(fd=fd, intrpr=intrpr)
            except RelathonException as e:
                fd.seek(0)
                cls.print_error(e, fd.read())

            fd.close()
            if imprt and exit_code == 0:
                return intrpr
            return exit_code

    @classmethod
    def print_error(self, error, source, prompt=False):
        """Print the error message to stderr."""
        print(error.get_message(source, prompt), file=sys.stderr)


def main(fd=None):
    if len(sys.argv) > 1:
        fd = sys.argv[1]
    return Relathon.run_in_main(fd)


def import_module(intrpr, symbol_table, module):
    """Load and run a module and import the symbols into the current
    environment.

    NOTE: This function gets called only from within the interpreter.
    """
    intrpr = Relathon.run_in_main(module, imprt=True, intrpr=intrpr)
    if type(intrpr) == int:
        sys.exit(intrpr)
    else:
        symbols = intrpr.current_env
        for sym, val in symbols.values.items():
            symbol_table.define(sym, val)


if __name__ == '__main__':
        sys.exit(main())