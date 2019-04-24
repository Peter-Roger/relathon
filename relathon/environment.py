# Copyright Peter Roger. All rights reserved.
#
# This file is part of relathon. Use of this source code is governed by
# the GPL license that can be found in the LICENSE file.

"""The enviroment keeps track of symbols defined in name space and
matters of scoping."""

from collections import OrderedDict

class Environment:
    """Environment namespace container that maps names to objects.

    Attributes:
        values (OrderedDict) - maps symbol names to values
        envName (str) - enviroment name
        envLevel (int) - indicates level of nesting
        enclosingEnv (Environment) - parent environment
    """

    def __init__(self, name="", level=0, enclosingEnv=None):
        self.values = OrderedDict()
        self.name = name
        self.level = level
        self.enclosingEnv = enclosingEnv

    def __str__(self):
        """Prints a nicely formatted human-readable table."""
        h1 = 'Environment (Scoped Symbol Table)'
        lines = ['\n', h1, '=' * len(h1)]
        for headerName, headerValue in (
            ('Env name', self.name),
            ('Env level', self.level),
            ('Enclosing env',
             self.enclosingEnv.name if self.enclosingEnv else None
            )
        ):
            lines.append('%-15s: %s' % (headerName, headerValue))

        h2 = 'Environment contents'
        lines.extend([h2, '-' * len(h2)])
        lines.extend(
            ('%7s: %r' % (key, value))
            for key, value in self.values.items()
        )
        lines.append('\n')
        s = '\n'.join(lines)
        return s

    __repr__ = __str__

    def define(self, name, value):
        """Add a symbol, value pair to the environment."""
        self.values[name] = value

    def resolve(self, name):
        """Get a value from the environment or parental environment."""
        value = self.values.get(name, False)
        if value is False and self.enclosingEnv is not None:
            value = self.enclosingEnv.resolve(name)
        return value