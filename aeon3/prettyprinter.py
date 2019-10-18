from aeon3.frontend_module.AeonASTVisitor import AeonASTVisitor

from aeon3.frontend_module.generated.AeonParser import AeonParser
from aeon3.frontend_module.generated.AeonLexer import AeonLexer

from .ast import *
from antlr4 import *
from .types import *

from .frontend import *

def printAST(node):

    print(type(node), node)

    if type(node) == Program:
        for decl in node.declarations:
            print(30 * '=')
            printAST(decl)

    elif type(node) == Hole:
        print(node.type)

    elif type(node) == Literal:
        print(node.value, type(node.value), node.type)

    elif type(node) == Var:
        print(node.name, node.type)

    elif type(node) == If:
        print("If statement: ", node.type)
        printAST(node.cond,)
        printAST(node.then)
        printAST(node.otherwise)

    elif type(node) == Application:
        print("Application statement: ", node.type)
        printAST(node.target)
        printAST(node.argument)

    elif type(node) == Abstraction:
        print("Abstraction statement: ", node.type)
        printAST(node.arg_name)
        printAST(node.body)

    elif type(node) == TAbstraction:
        printAST(node.typevar)
        printAST(node.kind)
        printAST(node.body)

    elif type(node) == TApplication:
        printAST(node.target)
        printAST(node.argument)

    elif type(node) == Definition:
        print("Definition statement: ", node.type)
        printAST(node.body)

    elif type(node) == TypeAlias:
        printAST(node.name)
        printAST(node.type)

    elif type(node) == TypeDeclaration:
        printAST(node.name)
        printAST(node.kind)

    elif type(node) == Import:
        printAST(node.name)
        if node.function is not None:
            printAST(node.function)

    elif type(node) == BasicType:
        print(node.name)

    elif type(node) == AbstractionType:
        print(node.arg_name)
        printAST(node.arg_type)
        printAST(node.return_type)

    elif type(node) == RefinedType:
        print(node.name, type(node.name))
        printAST(node.type)
        printAST(node.cond)
    
    elif type(node) == TypeAbstraction:
        printAST(node.name)
        printAST(node.kind)

    elif type(node) == TypeApplication:
        printAST(node.target)
        printAST(node.argument)

    elif type(node) == Kind:
        print(node)

    elif type(node) == str:
        print(node)

    else:
        print("Type of node not found: ", type(node), node)