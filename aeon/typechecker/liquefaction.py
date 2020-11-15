from aeon.libraries.stdlib import is_uninterpreted
from dataclasses import dataclass, replace
from typing import Optional, Callable

from ..types import ProductType, Type, BasicType, RefinedType, AbstractionType, TypeApplication, TypeAbstraction, \
    UnionType, IntersectionType, ExistentialType, TypeException, t_b, t_i, bottom, TypingContext, type_map, shape
from ..ast import TypedNode, Application, Abstraction, TApplication, TAbstraction, Literal, Var, If, Hole

from .substitutions import substitution_expr_in_expr, substitution_type_in_type, substitution_expr_in_type
from .exceptions import TypingException
from .type_simplifier import reduce_type
from .ast_helpers import smt_true, smt_and, smt_eq



remove_name = lambda name, lst: list(filter(lambda y: y[0] != name, lst))


def selfification(name:str, v, T):
    return Application(Application(Var("smtEq"), Var(name)), Literal(v, T))

def selfification_var(name:str, other_name:str):
    return Application(Application(Var("smtEq"), Var(name)), Var(other_name))

def replace_abstraction_type(vname:str, t:Type, arg:Type):
    if isinstance(t, BasicType):
        return None
    if isinstance(t, AbstractionType):
        return ExistentialType(vname, arg, substitution_expr_in_type(t.return_type, Var(vname), t.arg_name))
    if isinstance(t, ExistentialType):
        k = replace_abstraction_type(vname, t.right, arg)
        if k:
            return ExistentialType(t.left_name, t.left, k)
        else:
            print("oops")
            return None
    if isinstance(t, TypeApplication):
        """ A abstracção pode estar na aplicação ou só depois da substituição """
        if isinstance(t.target, TypeAbstraction):
            tr = replace_abstraction_type(vname, t.target.type, arg)
            if tr:
                return TypeApplication(TypeAbstraction(t.target.name, t.target.kind, tr), t.argument)
            else:
                return None # TODO
        else:
            return None
    if isinstance(t, TypeAbstraction):
        """ A abstracção pode estar na aplicação ou só depois da substituição """
        tr = replace_abstraction_type(vname, t.type, arg)
        if tr:
            return TypeAbstraction(t.name, t.kind, tr)
        else:
            return None # TODO

    raise Exception("Missing pattern in Liquefaction of rep", t)


@dataclass
class LiqExprResult:
    expr: Optional[TypedNode]
    ty: Type
    is_liquid: bool = False


def liquefaction_expr_w(ctx:TypingContext, e:TypedNode) -> LiqExprResult:
    if isinstance(e, Literal):
        if type(e.value) == bool:
            return LiqExprResult(Literal(e.value, t_b), RefinedType("_v", t_b, selfification("_v", e.value, t_b)), True)
        elif type(e.value) == int:
            return LiqExprResult(Literal(e.value, t_i), RefinedType("_v", t_i, selfification("_v", e.value, t_i)), True)
        else:
            return LiqExprResult(Literal(e.value, e.type), e.type) # TODO: String and Double
    elif isinstance(e, Var):
        t = ctx.variables[e.name]
        if isinstance(t, BasicType): # TODO: not a function!
            return LiqExprResult(Var(e.name), RefinedType("_v", t, selfification_var("_v", e.name)))
        elif e.name in ctx.uninterpreted_functions: # uninterpreted
            return LiqExprResult(Var(e.name), t, True)
        else:
            return LiqExprResult(None, t)
    elif isinstance(e, If):
        r1 = liquefaction_expr_w(ctx, e.cond)
        r2 = liquefaction_expr_w(ctx, e.then)
        r3 = liquefaction_expr_w(ctx, e.otherwise)
        return LiqExprResult(r1 and r2 and r3 and If(r1.expr, r2.expr, r3.expr), UnionType(r2.ty, r3.ty))
    elif isinstance(e, Application):
        e1 = liquefaction_expr_w(ctx, e.target)
        e2 = liquefaction_expr_w(ctx, e.argument)
        vname = ctx.fresh_var()
        if isinstance(e.target, Var):
            vname += "_" + str(e.target.name)
            #print("YELLOW F:", e.target.name)
        if isinstance(e.target, Application) and isinstance(e.target.target, Var):
            vname += "_" + str(e.target.target.name)
        #if vname.endswith("_fresh_300"):
        #    raise Exception(e1, e2) # TODO
        #print("will replace in vname", vname)
        #print("FTYPE:", e1.ty)
        #print("ATYPE", e2.ty)
        nt = replace_abstraction_type(vname, e1.ty, e2.ty)
        #print("RETURN:", nt)

        if not nt:
            raise Exception("Not implemented yet") # What (T:* -> T) [x:U -> V]

        if e1.is_liquid and e2.is_liquid:
            return LiqExprResult(Application(e1.expr, e2.expr), shape(nt), True)

        if e1.expr:
            if not e2.expr:
                e2.expr = Var(vname)
            return LiqExprResult(Application(e1.expr, e2.expr), nt)
        else:
            return LiqExprResult(None, nt)

    elif isinstance(e, Abstraction):
        t = liquefaction_ty_w(ctx, e.arg_type)
        eb = liquefaction_expr_w(ctx.with_var(e.arg_name, t), e.body)
        if eb:
            return LiqExprResult(None, AbstractionType(e.arg_name, t, eb.ty))
        else:
            return None
    elif isinstance(e, TAbstraction):
        t = liquefaction_expr_w(ctx, e.body)
        if t:
            return LiqExprResult(t.expr and TAbstraction(e.typevar, e.kind, t.expr), TypeAbstraction(e.typevar, e.king, t.ty))
        else:
            return None
    elif isinstance(e, TApplication):
        t = liquefaction_expr_w(ctx, e.target)
        if t:
            return LiqExprResult(t.expr and TApplication(t.expr, e.argument), TypeApplication(t.ty, e.argument))
        else:
            return None
    raise Exception("Missing pattern in Liquefaction of Expressions", e)


def liquefaction_ty_w(ctx:TypingContext, e:TypedNode) -> Type:
    if isinstance(e, BasicType):
        return BasicType(e.name)
    elif isinstance(e, AbstractionType):
        t1 = liquefaction_ty_w(ctx, e.arg_type)
        t2 = liquefaction_ty_w(ctx.with_var(e.arg_name, t1), e.return_type)
        return AbstractionType(e.arg_name, t1, t2)
    elif isinstance(e, RefinedType):
        t = liquefaction_ty_w(ctx, e.type)
        c = liquefaction_expr_w(ctx.with_var(e.name, t), e.cond)

        ori = c.ty
        #cty = type_map(lambda x: isinstance(x, RefinedType), lambda rec, rt: RefinedType(rt.name, rec(rt.type), smt_and(rt.cond, smt_eq(Var(rt.name), Var(e.name)))), c.ty)
        #print(" GO", ori, ">>", cty )
        if e.name == "x":
            print("C:", reduce_type(ctx, c.ty))
        if c:
            if c.expr:
                return RefinedType(e.name, IntersectionType(t, c.ty), c.expr)
            else:
                return IntersectionType(t, c.ty)
        else:
            return t
    elif isinstance(e, TypeAbstraction):
        t = liquefaction_ty_w(ctx, e.type)
        return TypeAbstraction(e.name, e.kind, t)
    elif isinstance(e, TypeApplication):
        t1 = liquefaction_ty_w(ctx, e.target)
        t2 = liquefaction_ty_w(ctx, e.argument)
        return TypeApplication(t1, t2)
    elif isinstance(e, UnionType):
        t1 = liquefaction_ty_w(ctx, e.left)
        t2 = liquefaction_ty_w(ctx, e.right)
        return UnionType(t1, t2)
    elif isinstance(e, IntersectionType):
        t1 = liquefaction_ty_w(ctx, e.left)
        t2 = liquefaction_ty_w(ctx, e.right)
        return IntersectionType(t1, t2)
    elif isinstance(e, ProductType):
        t1 = liquefaction_ty_w(ctx, e.left_type)
        t2 = liquefaction_ty_w(ctx.with_var(e.left_name, t1), e.right_type)
        return ProductType(e.left_name, t1, t2)
    elif isinstance(e, ExistentialType):
        t1 = liquefaction_ty_w(ctx, e.left_type)
        t2 = liquefaction_ty_w(ctx.with_var(e.left_name, t1), e.right_type)
        return ExistentialType(e.left_name, t1, t2)
    raise Exception("Missing pattern in Liquefaction of Types", e)


def liquefy_ctx(ctx:TypingContext):
    nctx = ctx.copy()
    for name in nctx.variables:
        nctx.variables[name] = liquefy_type(nctx, ctx.variables[name])
        #print("rvar", name, liquefy_type(nctx, ctx.variables[name]))
    for name in nctx.uninterpreted_functions:
        nctx.uninterpreted_functions[name] = liquefy_type(nctx, ctx.uninterpreted_functions[name])
        #print("uvar", name, liquefy_type(nctx, ctx.variables[name]))
    return nctx

def liquefy_type(ctx:TypingContext, t) -> Type:
    tp = liquefaction_ty_w(ctx, t)
    return reduce_type(ctx, tp)

def liquefy(ctx:TypingContext, t:Type) -> Type:
    c = liquefy_ctx(ctx.with_uninterpreted())
    return liquefy_type(c, t)

