from ..types import TypingContext, Kind, star, Type, BasicType, RefinedType, \
    AbstractionType, TypeAbstraction, TypeApplication, SumType, IntersectionType

from .exceptions import TypingException

# from .typing import checktype


class KindingError(TypingException):
    pass


def k_base(ctx: TypingContext, t: BasicType):
    if t.name in ['Boolean', 'Integer', 'Double', 'String', 'Top', 'Bottom']:
        return star
    elif t.name in ctx.type_variables:
        return ctx.type_variables[t.name]
    # TODO: Added this, check later
    elif t.name in ctx.type_aliases:
        return synth_kind(ctx, ctx.type_aliases[t.name])
    else:
        raise KindingError("{} is not a base type or in context".format(t))


def k_where(ctx: TypingContext, t: RefinedType):
    k = synth_kind(ctx, t.type)
    # TODO: problem with imports
    # checktype(ctx.with_var(t.name, t.type), t.cond, t_b)
    return k


def k_app(ctx: TypingContext, t: AbstractionType):
    check_kind(ctx, t.arg_type, star)
    check_kind(ctx.with_var(t.arg_name, t.arg_type), t.return_type, star)
    return star


def k_tapp(ctx: TypingContext, tapp: TypeApplication):
    mk = synth_kind(ctx, tapp.target)
    if mk == star:
        raise KindingError("{} does not have kind (k -> k')".format(
            tapp.target))
    assert (mk != star)
    check_kind(ctx, tapp.argument, mk.k1)
    return mk.k2


def k_tabs(ctx: TypingContext, tabs: TypeAbstraction):
    t = tabs.name
    k = tabs.kind
    T = tabs.type
    kp = synth_kind(ctx.with_type_var(t, k), T)
    return Kind(k, kp)


def k_sum(ctx: TypingContext, t: SumType):
    kl = synth_kind(ctx, t.left)
    kr = synth_kind(ctx, t.right)
    if kl != kr:
        raise KindingError("{} does not have consistent kinds".format(t))
    return kl


def k_intersection(ctx: TypingContext, t: IntersectionType):
    kl = synth_kind(ctx, t.left)
    kr = synth_kind(ctx, t.right)
    if kl != kr:
        raise KindingError("{} does not have consistent kinds".format(t))
    return kl


def synth_kind(ctx: TypingContext, t: Type) -> Kind:
    """ Γ ⸠ T => k """
    if isinstance(t, BasicType):
        return k_base(ctx, t)
    elif isinstance(t, RefinedType):
        return k_where(ctx, t)
    elif isinstance(t, AbstractionType):
        return k_app(ctx, t)
    elif isinstance(t, TypeAbstraction):
        return k_tabs(ctx, t)
    elif isinstance(t, TypeApplication):
        return k_tapp(ctx, t)
    elif isinstance(t, SumType):
        return k_sum(ctx, t)
    elif isinstance(t, IntersectionType):
        return k_intersection(ctx, t)
    raise KindingError("{} does not have a kind synthesis rule".format(t))


def check_kind(ctx: TypingContext, t: Type, e: Kind) -> Kind:
    """ Γ ⸠ T <= k """
    k = synth_kind(ctx, t)
    if k != e:
        raise KindingError("{}:{} does not have expected kind {}".format(
            t, k, e))
    return k
