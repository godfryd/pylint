# pylint: disable-msg=R0903
"""yo"""

__revision__ = '$I$'

class Aaaa:
    """class with attributes defined in wrong order"""
    def __init__(self):
        var1 = self._var2
        self._var2 = 3
        print var1

class Bbbb(object):
    """hop"""
    __revision__ = __revision__ # no problemo marge
