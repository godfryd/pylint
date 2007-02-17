# Copyright (c) 2003-2007 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""exceptions handling (raising, catching, exceptions classes) checker
"""

from logilab.common.compat import enumerate
from logilab import astng
from logilab.astng.inference import unpack_infer

from pylint.checkers import BaseChecker
from pylint.checkers.utils import is_empty, is_raising
from pylint.interfaces import IASTNGChecker

MSGS = {
    'E0701': (
    'Bad except clauses order (%s)',
    'Used when except clauses are not in the correct order (from the \
    more specific to the more generic). If you don\'t fix the order, \
    some exceptions may not be catched by the most specific handler.'),
    'E0702': ('Raising %s while only classes, instances or string are allowed',
              'Used when something which is neither a class, an instance or a \
              string is raised (i.e. a `TypeError` will be raised).'),
    
    'W0701': ('Raising a string exception',
              'Used when a string exception is raised.'),
    'W0702': ('No exception\'s type specified',
              'Used when an except clause doesn\'t specify exceptions type to \
              catch.'),
    'W0703': ('Catch "Exception"',
              'Used when an except catch Exception instances.'),
    'W0704': ('Except doesn\'t do anything',
              'Used when an except clause does nothing but "pass" and there is\
              no "else" clause.'),
    'W0706': (
    'Identifier %s used to raise an exception is assigned to %s',
    'Used when a variable used to raise an exception is initially \
    assigned to a value which can\'t be used as an exception.'),
    }
    
class ExceptionsChecker(BaseChecker):
    """checks for                                                              
    * excepts without exception filter                                         
    * string exceptions                                                        
    """
    
    __implements__ = IASTNGChecker

    name = 'exceptions'
    msgs = MSGS
    priority = -4
    options = ()

    def visit_raise(self, node):
        """check for string exception
        """
        # ignore empty raise
        if node.expr1 is None:
            return
        expr = node.expr1
        if isinstance(expr, astng.Const):
            value = expr.value
            if isinstance(value, str):
                self.add_message('W0701', node=node)
            else:
                self.add_message('E0702', node=node,
                                 args=value.__class__.__name__)
        elif isinstance(expr, astng.Name) and \
                 expr.name in ('None', 'True', 'False'):                
            self.add_message('E0702', node=node, args=expr.name)
        elif isinstance(expr, astng.Mod):
            self.add_message('W0701', node=node)
        else:
            try:
                value = unpack_infer(expr).next()
            except astng.InferenceError:
                return
            # have to be careful since Const, Dict, .. inherit from
            # Instance now and get the original astng class as _proxied
            if (value is astng.YES or
                isinstance(value, (astng.Class, astng.Module)) or
                (isinstance(value, astng.Instance) and 
                 isinstance(value._proxied, astng.Class) and
                 value._proxied.root().name != '__builtin__')):
                return
            if isinstance(value, astng.Const) and \
               (value.value is None or 
                value.value is True or value.value is False):
                # this Const has been generated by resolve
                # since None, True and False are represented by Name
                # nodes in the ast, and so this const node doesn't
                # have the necessary parent, lineno and so on attributes
                assinfo = value.as_string()
            else:
                assinfo = '%s line %s' % (value.as_string(),
                                          value.source_line())
            self.add_message('W0706', node=node,
                             args=(expr.as_string(), assinfo))
            
    def visit_tryexcept(self, node):
        """check for empty except
        """
        exceptions_classes = []
        nb_handlers = len(node.handlers)
        for index, handler  in enumerate(node.handlers):
            exc_type = handler[0]
            stmt = handler[2]
            # single except doing nothing but "pass" without else clause
            if nb_handlers == 1 and is_empty(stmt) and not node.else_:
                self.add_message('W0704', node=exc_type or stmt)
            if exc_type is None:
                if nb_handlers == 1 and not is_raising(stmt):
                    self.add_message('W0702', node=stmt.nodes[0])
                # check if a "except:" is followed by some other
                # except
                elif index < (nb_handlers - 1):
                    msg = 'empty except clause should always appears last'
                    self.add_message('E0701', node=node, args=msg)
            else:
                try:
                    excs = list(unpack_infer(exc_type))
                except astng.InferenceError:
                    continue
                for exc in excs:
                    # XXX skip other non class nodes 
                    if exc is astng.YES or not isinstance(exc, astng.Class):
                        continue
                    exc_ancestors = [anc for anc in exc.ancestors()
                                     if isinstance(anc, astng.Class)]
                    for previous_exc in exceptions_classes:
                        if previous_exc in exc_ancestors:
                            msg = '%s is an ancestor class of %s' % (
                                previous_exc.name, exc.name)
                            self.add_message('E0701', node=exc_type, args=msg)
                    if (exc.name == 'Exception'
                        and exc.root().name == 'exceptions'
                        and nb_handlers == 1 and not is_raising(stmt)):
                        self.add_message('W0703', node=exc_type)
                exceptions_classes += excs
        
def register(linter):
    """required method to auto register this checker"""
    linter.register_checker(ExceptionsChecker(linter))
