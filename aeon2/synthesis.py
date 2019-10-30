import random
import string
import sys

from .ast import Var, TAbstraction, TApplication, Application, Abstraction, Literal, Hole, If, Program, \
    TypeDeclaration, TypeAlias, Definition
from .types import TypingContext, Type, BasicType, RefinedType, AbstractionType, TypeAbstraction, \
    TypeApplication, Kind, AnyKind, star, TypeException, t_b, t_i
from .substitutions import substitution_expr_in_type, substitution_type_in_type, \
    substitution_expr_in_expr, substitution_type_in_expr
import aeon2.typechecker as tc

forbidden_vars = ['native', 'uninterpreted']

weights = {
    "sk_star": 1,  # Kinding
    "sk_rec": 0,
    "st_int": 1,  # Terminal types
    "st_bool": 1,
    "se_int": 1,  # Terminal types
    "se_bool": 1,
    "se_var": 1,
    "se_where": 1,
    "se_abs": 1,
    "se_app": 1,
    "se_tabs": 1,
    "stax_id": 1,
    "stax_id": 1,
}


def set_weights(w):
    for k in w:
        weights[k] = w[k]


class Unsynthesizable(Exception):
    pass


def pick_one_of(alts):
    total = sum([weights[v[0]] for v in alts])
    i = random.randint(0, total - 1)
    for (prob, choice) in alts:
        i -= weights[prob]
        if i <= 0:
            return choice
    print("BIG FAIL")


def random_chooser(f):
    def f_alt(*args, **kwargs):
        random.seed(random.randint(0, 1030))
        valid_alternatives = list(f(*args, *kwargs))
        if not valid_alternatives:
            raise Unsynthesizable(*args)
        while True:
            fun = pick_one_of(valid_alternatives)
            try:
                return fun(*args, **kwargs)
            except Exception as e:
                print("Exception:", e)
                print("Failed once to pick using", fun)
                continue

    return f_alt


""" Kind synthesis """


@random_chooser
def sk(d=5):
    """ ~> k """
    yield ("sk_star", lambda d: star)
    if d >= 1:
        yield ("sk_rec", lambda d: Kind(sk(d - 1), sk(d - 1)))


""" Type Synthesis """


@random_chooser
def st(ctx, k, d):
    """ Γ ⸠ k ~>_{d} T """
    if k == star:
        yield ("st_int", lambda ctx, k, d: t_i)
    if k == star:
        yield ("st_bool", lambda ctx, k, d: t_b)
    # TODO


def fv(T):
    if type(T) is RefinedType:
        return [T.name] + fv(T.type)
    if type(T) is AbstractionType:
        return [T.arg_name] + fv(T.arg_type) + fv(T.return_type)
    return []


def scfv(T):
    """ ~fv(T) ~> t """
    freevars = fv(T)
    w = ""
    for i in range(1000):
        w += random.choice(string.ascii_letters)
        if w not in freevars:
            return w
    return "_qwerty"


def get_variables_of_type(ctx, T):
    return [
        v for v in ctx.variables
        if tc.is_subtype(ctx, ctx.variables[v], T) and v not in forbidden_vars
    ]


""" Expression Synthesis """


def se_bool(ctx, T, d):
    """ SE-Bool """
    v = random.random() < 0.5
    return Literal(v, type=T)


def se_int(ctx, T, d):
    """ SE-Int """
    v = random.randint(-100, 100)
    name = "lit_{}".format(v)
    return Literal(v,
                   type=RefinedType(name=name,
                                    type=T,
                                    cond=Application(
                                        Application(Var("=="), Var(name)),
                                        Literal(value=v,
                                                type=t_i,
                                                ensured=True))))


def se_if(ctx, T, d):
    """ SE-If """
    cond = se(ctx, t_b, d - 1)
    then = se(ctx, T, d - 1)  # missing refinement in type
    otherwise = se(ctx, T, d - 1)  # missing refinement in type
    return If(cond, then, otherwise).with_type(T)


def se_var(ctx, T, d):
    """ SE-Var """
    options = get_variables_of_type(ctx, T)
    if options:
        n = random.choice(options)
        return Var(n).with_type(T)
    raise Unsynthesizable("No var of type {}".format(T))


def se_abs(ctx, T: AbstractionType, d):
    """ SE-Abs """
    nctx = ctx.with_var(T.arg_name, T.arg_type)
    body = se(nctx, T.return_type, d - 1)
    print("Body:", body, " return type", T.return_type, "type", T)
    return Abstraction(T.arg_name, T.arg_type, body).with_type(T)


def se_where(ctx, T: RefinedType, d):
    """ SE-Where """
    for _ in range(100):
        e2 = se(ctx, T.type, d - 1)
        ncond = substitution_expr_in_expr(T.cond, e2, T.name)
        if tc.entails(ctx, ncond):
            return e2.with_type(T)
    raise Unsynthesizable("Bug in se_where: {}".format(T))


def se_tabs(ctx, T: TypeAbstraction, d):
    """ SE-TAbs """
    nctx = ctx.with_type_var(T.name, T.kind)
    e = se(nctx, T.type, d - 1)
    return TAbstraction(T.name, T.kind, e).with_type(T)


def se_app(ctx, T, d):
    """ SE-App """
    k = sk(d)
    U = st(ctx, k, d - 1)
    x = scfv(T)
    e2 = se(ctx, U, d - 1)

    nctx = ctx.with_type_var(x, U)
    V = stax(nctx, e2, x, T, d - 1)
    FT = AbstractionType(arg_name=x, arg_type=U, return_type=V)
    print("last one", FT)
    e1 = se(ctx, FT, d - 1)
    print("after", e1)
    return Application(e1, e2).with_type(T)


@random_chooser
def se(ctx, T, d):
    """ Γ ⸠ T~>_{d} e """
    if type(T) is BasicType and T.name == "Integer":
        yield ("se_int", se_int)
    if type(T) is BasicType and T.name == "Boolean":
        yield ("se_bool", se_bool)
    if get_variables_of_type(ctx, T):
        yield ("se_var", se_var)
    if d > 0:
        # TODO
        # yield (1, lambda: se_if(ctx, T, d))
        if type(T) is AbstractionType:
            yield ("se_abs", se_abs)
        if type(T) is RefinedType:
            print("WHERE")
            yield ("se_where", se_where)
        if type(T) is TypeAbstraction:
            yield ("se_tabs", se_tabs)
        yield ("se_app", se_app)
        """ TODO: SE-TApp """


""" Expression Synthesis parameterized with x:T """


def stax_id(nctx, e, x, T, d):
    """ STAx-Id """
    return T


@random_chooser
def stax(ctx, e, x, T, d):
    """ Γ ⸠ T ~>_{d} U """
    #yield (1, lambda: stax_id(nctx, e, x, T, d))
    yield (1, lambda ctx, e, x, T, d: T)
    """ TODO: STAx-Arrow """
    """ TODO: STAx-App """
    """ TODO: STAx-Abs """
    """ TODO: STAx-Where """
