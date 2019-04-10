# Copyright Peter Roger. All rights reserved.
#
# This file is part of relathon. Use of this source code is governed by
# the GPL license that can be found in the LICENSE file.

class Location:

    def __init__(self, filename, pos, lineBegin, columnBegin, lineEnd, columnEnd):
        self.filename = filename
        self.pos = pos
        self.lineBegin = lineBegin
        self.columnBegin = columnBegin
        self.lineEnd = lineEnd
        self.columnEnd = columnEnd

    def __repr__(self):
        return "{}({}, {}, {}, {}, {}, {})".format(self.__class__.__name__, self.filename, self.pos, self.lineBegin, self.columnBegin, self.lineEnd, self.columnEnd)

    def __str__(self):
        return "{}:{} {}.{}-{}.{}".format(self.filename, self.pos, self.lineBegin,
                                       self.columnBegin, self.lineEnd,
                                       self.columnEnd)

    def __eq__(self, other):

        return isinstance(other, Location) and (self.filename, self.pos, self.lineBegin, self.columnBegin, self.lineEnd, self.columnEnd) == \
            (other.filename, other.pos, other.lineBegin, other.columnBegin, other.lineEnd, other.columnEnd)

    def combine(self, other):
        assert self.filename == other.filename
        pos = min(self.pos, other.pos)
        lineBegin, columnBegin = min((self.lineBegin, self.columnBegin),
                                (other.lineBegin, other.columnBegin))
        lineEnd, columnEnd = max((self.lineEnd, self.columnEnd),
                            (other.lineEnd, other.columnEnd))
        return Location(self.filename, pos, lineBegin, columnBegin, lineEnd, columnEnd)

NoLoc = Location("<unknown>", 0, 0, 0, 0, 0)