# Copyright Peter Roger. All rights reserved.
#
# This file is part of relathon. Use of this source code is governed by
# the GPL license that can be found in the LICENSE file.

"""The enviroment keeps track of symbols defined in name space and
matters of scoping."""

from collections import OrderedDict

class Environment:
    """Namespace container that maps names to objects.

    Attributes:
        values (OrderedDict) - maps symbol names to values
        envName (str) - enviroment name
        envLevel (int) - indicates level of nesting
        enclosingEnv (Environment) - parent environment
    """

    def __init__(self, envName="", envLevel=0, enclosingEnv=None):
        self.values = OrderedDict()
        self.envName = envName
        self.envLevel = envLevel
        self.enclosingEnv = enclosingEnv

    def __str__(self):
        """Prints a nicely formatted human-readable table."""
        h1 = 'SCOPE (SCOPED SYMBOL TABLE)'
        lines = ['\n', h1, '=' * len(h1)]
        for headerName, headerValue in (
            ('Scope name', self.envName),
            ('Scope level', self.envLevel),
            ('Enclosing scope',
             self.enclosingEnv.envName if self.enclosingEnv else None
            )
        ):
            lines.append('%-15s: %s' % (headerName, headerValue))

        h2 = 'Scope (Scoped symbol table) contents'
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
        """Get a value from the environment or parent environments."""
        value = self.values.get(name, False)
        if value is False and self.enclosingEnv is not None:
            value = self.enclosingEnv.resolve(name)
        return value