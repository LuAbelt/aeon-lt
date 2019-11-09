from .types import TypingContext, Type, BasicType, RefinedType, AbstractionType, TypeAbstraction, \
    TypeApplication, Kind, AnyKind, star, TypeException, t_b, t_delegate
from .ast import Var, TAbstraction, TApplication, Application, Abstraction, Literal
from .substitutions import substitution_expr_in_type, substitution_type_in_type, \
    substitution_expr_in_expr, substitution_type_in_expr
from .synthesis import *
from .zed import zed_verify_entailment, zed_verify_satisfiability, zed_get_integer_where, NotDecidableException

def flatten_refined_type(t:Type):
    if isinstance(t, BasicType):
        return t
    if isinstance(t, RefinedType):
        return flatten_refined_type(t.type)
    print("FAIL")




def is_same_type(ctx, a, b):
    return is_subtype(ctx, a, b) and is_subtype(ctx, b, a)


def c_beta_simplication(ctx: TypingContext, t: Type, k: Kind):
    """ Reduces a type according to C-Beta """
    if isinstance(t, TypeApplication):
        starget = c_beta_simplication(ctx, t.target, AnyKind())
        sargument = c_beta_simplication(ctx, t.argument, AnyKind())

        if isinstance(starget, TypeAbstraction):
            small_t = starget.name
            small_k = starget.kind
            big_t = starget.type

            return substitution_type_in_type(big_t, sargument, small_t)
    return t


def s_cong(ctx: TypingContext, sub: Type, sup: Type, k: Kind):
    """"  Type Conversion  """
    if isinstance(sub, BasicType):
        if sub.name in ctx.type_aliases:
            return s_cong(ctx, ctx.type_aliases[sub.typeName], sup, k)
    if isinstance(sup, BasicType):
        if sup.name in ctx.type_aliases:
            return s_cong(ctx, sub, ctx.type_aliases[sup.typeName], k)

    sub = c_beta_simplication(ctx, sub, k)
    sup = c_beta_simplication(ctx, sup, k)
    """ C-Ref """
    if isinstance(sub, BasicType) and type(
            sup) is BasicType and sub.name == sup.name:
        k2 = kinding(ctx, sub, k)
        return True
    return False


def is_subtype(ctx, sub, sup):
    """ Subtyping Rules """
    if isinstance(sub, BasicType):
        if sub.name == 'Bottom':
            return True  # Bottom
        if sub.name in ctx.type_aliases:
            return is_subtype(ctx, ctx.type_aliases[sub.typeName], sup)
    if isinstance(sup, BasicType):
        if sup.name in ['Void', 'Object', 'Top']:
            return True  # Top
        if sup.name in ctx.type_aliases:
            return is_subtype(ctx, sub, ctx.type_aliases[sup.typeName])

    if isinstance(sub, BasicType):
        if sub.name in ['Void', 'Object', 'Top']:
            return False  # Top
    if isinstance(sup, BasicType):
        if sup.name == 'Bottom':
            return False  # Bottom

    if isinstance(sub, BasicType) and isinstance(sup, BasicType):
        return sub_base(ctx, sub, sup)
    if isinstance(sup, RefinedType):
        return sub_whereR(ctx, sub, sup)
    if isinstance(sub, RefinedType):
        return sub_whereL(ctx, sub, sup)
    if isinstance(sub, AbstractionType) and isinstance(sup, AbstractionType):
        return sub_abs(ctx, sub, sup)
    if isinstance(sub, TypeAbstraction) and isinstance(sup, TypeAbstraction):
        return sub_tabs(ctx, sub, sup)

    return s_cong(ctx, sub, sup, AnyKind())
    raise Exception('No subtyping rule for {} <: {}'.format(sub, sup))


def extract_clauses(t):
    if isinstance(t, RefinedType):
        return [t.cond] + extract_clauses(t.type)
    return []


def expr_eval(ctx, t: RefinedType):
    conditions = extract_clauses(t)
    return is_satisfiable(ctx, conditions)


def entails(ctx, cond):
    return zed_verify_entailment(ctx, cond)
    """Disable for synthesis:
    cond_type = tc(ctx, cond).type
    if not is_subtype(ctx, cond_type, t_b):
        raise TypeException(
            'Clause not boolean',
            "Condition {}:{} is not a boolean expression".format(cond, cond_type))
    else:
        return zed_verify_entailment(ctx, cond)
    """


def get_integer_where(ctx: TypingContext, name: str, cond):
    return zed_get_integer_where(ctx, name, cond)


def is_satisfiable(ctx, cond):
    #cond_type = tc(ctx, cond).type
    if False:  #not is_subtype(ctx, cond_type, t_b):
        raise TypeException(
            'Clause not boolean',
            "Condition {} is not a boolean expression".format(cond))
    else:
        try:
            #cond = tc(ctx, cond)
            return zed_verify_satisfiability(ctx, cond)
        except NotDecidableException:
            return True


def k_base(ctx, t, k: Kind):
    """ K-Int, K-Bool and K-Var """
    if t in ctx.type_variables:
        expected_kind = ctx.type_variables[t]
        if k != expected_kind:
            raise TypeException(
                "Wrong kinding",
                "{} has kind *. {} given instead.".format(t, k))
    else:
        raise TypeException("Unknown type {} of kind {}".format(t, k))
    return expected_kind


def k_abs(ctx, t: AbstractionType, k: Kind):
    """ K-Abs """
    x = t.arg_name
    T = t.arg_type
    U = t.return_type
    kinding(ctx, T, star)
    kinding(ctx.with_var(x, T), U, star)
    if not isinstance(k, AnyKind) and k != star:
        raise TypeException("Type has wrong kinding.",
                            "Expected {}, given {}.".format(star, t))
    return star


def k_where(ctx, t: RefinedType, k: Kind):
    """ K-Where """
    t.cond = tc(ctx.with_var(t.name, t.type), t.cond, expects=t_b)
    return kinding(ctx, t.type, k)


def k_tabs(ctx, t: TypeAbstraction, k: Kind):
    """ K-TAbs """
    if type(k) != AnyKind:
        if k == star:
            raise TypeException("Type Abstraction cannot be of Kind *")

        if t.kind != k.k1:
            raise TypeException(
                "Argument of TypeAbstraction {} is not {}.".format(
                    t.kind, k.k1))

        k2 = kinding(ctx.with_type_var(BasicType(t.name), t.kind), t.type,
                     k.k2)
        if k2 != k.k2:
            raise TypeException(
                "Body of TypeAbstraction {} (kind: {}) is not of kind {}.".
                format(t, k2, k.k2))
    else:
        k2 = kinding(ctx.with_type_var(BasicType(t.name), t.kind), t.type, k)

    return Kind(k1=t.kind, k2=k2)


def k_tapp(ctx, t: TypeApplication, k: Kind):
    """ K-TApp """
    T = t.target
    U = t.argument
    k1 = kinding(ctx, U, AnyKind())
    k_a = kinding(ctx, T, Kind(k1=k1, k2=AnyKind()))
    if k != k_a.k2:
        raise TypeException(
            "Type Abstraction has wrong kinding.\nExpected {}, given {}.".
            format(k, k_a.k2))
    return k_a.k2


def kinding(ctx, t: Type, k: Kind):
    if isinstance(t, BasicType):
        return k_base(ctx, t, k)
    elif isinstance(t, AbstractionType):
        return k_abs(ctx, t, k)
    elif isinstance(t, RefinedType):
        return k_where(ctx, t, k)
    elif isinstance(t, TypeAbstraction):
        return k_tabs(ctx, t, k)
    elif isinstance(t, TypeApplication):
        return k_tapp(ctx, t, k)
    raise Exception('No kinding rule for {}'.format(t))


## HELPERS:


def check_expects(ctx, n, expects):
    if expects != None:
        if not hasattr(n, "type"):
            raise TypeException('Node {} with unknown type'.format(n, type(n)),
                                expected=expects,
                                given=n.type)

        if not is_subtype(ctx, n.type, expects):
            raise TypeException(
                '{} has wrong type'.format(type(n)),
                "{} has wrong type (given: {}, expected: {})".format(
                    n, n.type, expects),
                expected=expects,
                given=n.type)


# Expression TypeChecking


def expr_has_type(ctx, e, t):
    """ E-Subtype """
    if not hasattr(e, "type") or e.type == None:
        tc(ctx, e, expects=t)
    if e.type == t:
        return True

    if isinstance(t, RefinedType):
        """ T-Where """
        ne = substitution_expr_in_expr(t.cond, e, t.name)
        return expr_has_type(ctx, e, t.type) and entails(ctx, ne)

    return kinding(ctx, e.type, AnyKind()) and is_subtype(ctx, e.type, t)


def t_literal(ctx, n, expects=None):
    """ T-Bool, T-Int, T-Basic """
    # Literals have their type filled
    if not n.type and not n.ensured:
        name = "Literal_{}".format(n.value)
        if type(n.value) == bool:
            btype = t_b
            op = "==="
        else:
            btype = t_i
            op = "=="
        n.type = RefinedType(name=name,
                             type=btype,
                             cond=Application(
                                 Application(Var(op), Var(name)),
                                 Literal(value=n.value,
                                         type=btype,
                                         ensured=True)))

    return n


def t_var(ctx, n, expects=None):
    """ T-Var """
    if n.name not in list(ctx.variables):
        raise Exception(
            'Unknown variable',
            "Unknown variable {}.\n {}".format(n.name, list(ctx.variables)))
    n.type = ctx.variables[n.name]
    return n


def t_if(ctx, n, expects=None):
    """ T-If """
    n.cond = tc(ctx, n.cond, expects=t_b)
    n.then = tc(ctx, n.then, expects=expects)  # TODO: Missing context clauses
    n.otherwise = tc(ctx, n.otherwise, expects=expects)  # TODO: same
    if expects:
        n.type = expects
    else:
        n.type = n.then.type  # TODO - missing least common supertype else
    return n


def t_abs(ctx, n, expects=None):
    """ T-Abs """
    if expects and isinstance(expects, AbstractionType):
        body_expects = substitution_expr_in_type(expects.return_type,
                                                 Var(n.arg_name),
                                                 expects.arg_name)
    else:
        body_expects = None

    nctx = ctx.with_var(n.arg_name, n.arg_type)
    n.body = tc(nctx, n.body, expects=body_expects)
    n.type = AbstractionType(arg_name=n.arg_name,
                             arg_type=n.arg_type,
                             return_type=n.body.type)
    return n


def t_app(ctx, n: Application, expects=None):
    """ T-App """

    if type(n.target) is TApplication and n.target.argument == t_delegate:
        n.argument = tc(ctx, n.argument, expects=None)
        n.target.argument = flatten_refined_type(n.argument.type)

    n.target = tc(ctx, n.target, expects=None)
    n.target.type = c_beta_simplication(ctx, n.target.type, AnyKind())

    if type(n.target.type) is AbstractionType:
        ftype = n.target.type
        nctx = ctx.with_var(n.target.type.arg_name, n.target.type.arg_type)
        n.argument = tc(ctx, n.argument, expects=ftype.arg_type)
        print("type of app", n, "is", ..)
        n.type = substitution_expr_in_type(ftype.return_type, n.argument,
                                           n.target.type.arg_name)
        print("type of app", n, "is", n.type)
        return n
    else:
        raise TypeException(
            'Not a function',
            "{} does not have the right type (had {}, expected {})".format(
                n, n.target.type, expects),
            expects=expects,
            given=n.target.type)


def t_tabs(ctx, n: TAbstraction, expects: Type = None):
    """ E-TAbs """
    a_expects = None
    if expects and isinstance(expects, TypeAbstraction):
        a_expects = expects.type
    nctx = ctx.with_type_var(n.typevar, n.kind)
    n.body = tc(nctx, n.body, a_expects)
    n.type = TypeAbstraction(name=n.typevar, kind=n.kind, type=n.body.type)
    return n


def e_tapp(ctx, tapp: TApplication, expects=None):
    """ E-TApp """
    tc(ctx, tapp.target)
    target_type = c_beta_simplication(ctx, tapp.target.type, k=AnyKind())
    if not isinstance(target_type, TypeAbstraction):  # TODO C-Beta
        raise TypeException('Not a type function',
                            "{} does not have the right type: {} (expecting: {})".format(tapp, target_type, expects),
                            expects=expects,
                            given=tapp.target.type)

    tabs: TypeAbstraction = tapp.target.type
    t, k, U = tabs.name, tabs.kind, tabs.type
    T = tapp.argument
    tapp.type = substitution_type_in_type(U, T, t)
    return tapp


def tc(ctx, n, expects=None):
    """ TypeChecking AST nodes. Expects make it bidirectional """
    if isinstance(n, list):
        return [tc(ctx, e) for e in n]
    elif isinstance(n, Hole):
        n = synthesize(ctx, n.type)
    elif isinstance(n, Literal):
        n = t_literal(ctx, n, expects)
    elif isinstance(n, Var):
        n = t_var(ctx, n, expects)
    elif isinstance(n, If):
        n = t_if(ctx, n, expects)
    elif isinstance(n, Application):
        n = t_app(ctx, n, expects)
    elif isinstance(n, Abstraction):
        n = t_abs(ctx, n, expects)
    elif isinstance(n, TApplication):
        n = e_tapp(ctx, n, expects)
    elif isinstance(n, TAbstraction):
        n = t_tabs(ctx, n, expects)
    elif isinstance(n, Program):
        n.declarations = tc(ctx, n.declarations)
    elif isinstance(n, TypeDeclaration):
        ctx.add_type_var(n.name, n.kind)
    elif isinstance(n, TypeAlias):
        ctx.type_aliases[n.name] = n.type
    elif isinstance(n, Definition):
        k = kinding(ctx, n.type, AnyKind())
        name = n.name
        body = n.body
        ctx.variables[name] = n.type
        n.body = tc(ctx, body, expects=n.type)
    else:
        print("Could not typecheck {} of type {}".format(n, type(n)))
    check_expects(ctx, n, expects)
    return n


def typecheck(program, refined=True, synthesiser=None):
    ctx = TypingContext()
    ctx.setup()
    return tc(ctx, program), ctx, None


def synthesize(ctx, t):
    d = 1
    print(", ".join(list(ctx.variables.keys())), "|-", t, " ~> _", 3)
    n = se(ctx, t, 3)
    print(20 * "-")
    n = tc(ctx, n, t)
    print(n, ":", n.type)
    return n