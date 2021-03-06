u"""
Fixer for:

def something(self):
    super()

->

def something(self):
    super(self.__class__, self)
"""

from lib2to3 import fixer_base
from ..fixer_util import Node, Leaf, token, syms, Name, Comma, Dot

dot_class = Node(syms.trailer, [Dot(), Name(u"__class__")])


def get_firstparam(super_node):
    parent = super_node.parent
    while parent.type != syms.funcdef and parent.parent:
        parent = parent.parent

    if parent.type != syms.funcdef:
        # super() called without arguments outside of a funcdef
        return None

    children = parent.children
    assert len(children) > 2
    params = children[2]
    assert params.type == syms.parameters
    if len(params.children) < 3:
        # Function has no parameters, therefore super() makes no sense here...
        return None
    args = params.children[1]
    if args.type == token.NAME:
        return args.value
    elif args.type == syms.typedargslist:
        assert len(args.children) > 0
        if args.children[0].type == token.NAME:
            return args.children[0].value
        else:
            # Probably a '*'
            return None


def insert_args(name, rparen):
    parent = rparen.parent
    idx = parent.children.index(rparen)
    parent.insert_child(idx, Name(name, prefix=u" "))
    parent.insert_child(idx, Comma())
    parent.insert_child(idx, Node(syms.power, [Name(name), dot_class.clone()]))


class FixSuper(fixer_base.BaseFix):

    PATTERN = u"power< 'super' trailer< '(' rparen=')' > any* >"

    def transform(self, node, results):
        param = get_firstparam(node)
        if param is None:
            self.cannot_convert(
                node, u"super() with no arguments must be called inside a function that has at least one parameter")
            return
        rparen = results[u"rparen"]
        insert_args(param, rparen)
