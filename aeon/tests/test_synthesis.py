import unittest
import random

from ..types import TypingContext, Kind, star, Type
from ..frontend_core import expr, typee
from ..synthesis.synthesis import sk, se, se_bool, se_int, se_var, se_app, \
    se_where, iet, se_app_in_context, se_abs, Unsynthesizable
from ..typechecker import check_type, is_subtype, TypeCheckingError

ex = expr.parse
ty = typee.parse


class TestSynthesis(unittest.TestCase):
    def setUp(self):
        random.seed(0)

    def assert_st(self, ctx, sub, sup):
        if not is_subtype(ctx, sub, sup):
            raise AssertionError(sub, "is not subtype of", sup)

    def assert_synth(self, ctx, t, times=3, fun=se, d=None):
        if not isinstance(t, Type):
            t = ty(t)
        if d == None:
            d = 5
        print("----")
        foundCount = 0
        for i in range(times):
            try:
                e = fun(ctx, t, d)
                print(t, "~>", e)
                try:
                    check_type(ctx, e, t)
                except TypeCheckingError as ex:
                    self.fail("TypeChecking failed for {} : {} ||| {}".format(
                        e, t, ex))
                self.assert_st(ctx, e.type, t)
                foundCount += 1
            except Unsynthesizable as e:
                raise e
                pass
        if foundCount < times:
            self.fail("Failed to find an instance of type {} ({}/{})".format(
                t, foundCount, times))

    def generic_test(self, t, fun=None, extra_ctx=None, d=None, times=10):
        if not fun:
            fun = se
        ctx = TypingContext()
        ctx.setup()
        if extra_ctx:
            for (k, v) in extra_ctx:
                if v.startswith('type'):
                    ctx = ctx.with_type_var(v, "*")
                else:
                    ctx = ctx.with_var(k, ty(v))
        self.assert_synth(ctx, t, fun=fun, d=d, times=times)

    def test_synthesis_kind_1(self):
        ctx = TypingContext()
        ctx.setup()
        self.assertEqual(sk(0), star)

    def test_synthesis_kind_2(self):
        ctx = TypingContext()
        ctx.setup()
        self.assertIn(sk(1), [star, Kind(star, star)])

    def test_synthesis_kind_3(self):
        ctx = TypingContext()
        ctx.setup()
        self.assertIsInstance(sk(5), Kind)

    def test_bool(self):
        self.generic_test("Boolean", fun=se_bool, d=1)

    def test_int(self):
        self.generic_test("Integer", fun=se_int, d=1)

    def test_big_int(self):
        self.generic_test("Integer",
                          fun=se_app_in_context,
                          d=7,
                          times=1,
                          extra_ctx=[("f", "(i:Integer) -> Integer")])

    def test_big_int2(self):
        self.generic_test("{x:Integer | x > 0}",
                          fun=se_app_in_context,
                          d=7,
                          times=1,
                          extra_ctx=[
                              ("f", "(i:Integer) -> {z:Integer | z == i + 1}")
                          ])

    def test_var(self):
        self.generic_test("Integer",
                          fun=se_var,
                          d=1,
                          extra_ctx=[("x", "Integer")])

    def test_var_2(self):
        self.generic_test("Boolean",
                          fun=se_var,
                          d=1,
                          extra_ctx=[("x", "Boolean")])

    def test_var_3(self):
        self.generic_test("Integer",
                          fun=se_var,
                          d=1,
                          extra_ctx=[("x", "{x:Integer where (x > 3)}")])

    def test_var_4(self):
        self.generic_test("{y:Integer where (y > 2)}",
                          fun=se_var,
                          d=1,
                          extra_ctx=[("x", "{x:Integer where (x > 3)}")])

    def test_where(self):
        self.generic_test("{y:Integer where (y > 2)}")

    def test_g_bool(self):
        self.generic_test("Boolean")

    def test_g_bool_false(self):
        self.generic_test("{x:Boolean where (x == false)}", fun=se_where)

    def test_g_int(self):
        self.generic_test("Integer")

    def test_g_pos(self):
        self.generic_test("{x:Integer where (x > 0)}")

    def test_g_m4(self):
        self.generic_test("{x:Integer where ((x % 4) == 0)}")

    def test_g_m4_gt2(self):
        self.generic_test("{x:Integer where (((x % 4) == 0) && (x > 2))}")

    def test_g_abs(self):
        self.generic_test("(x:Boolean) -> Integer", d=10, fun=se_abs)

    def test_g_abs_with_var(self):
        self.generic_test("(x:Boolean) -> Integer",
                          d=1,
                          extra_ctx=[("z", "(x:Boolean) -> Integer")])

    def test_g_abs_with_var_2(self):
        self.generic_test("(x:Boolean) -> Integer",
                          extra_ctx=[("z", "{k:Integer where (k > 0)}")])

    def test_g_where(self):
        self.generic_test("{x:Integer where (x > 0)}")

    def test_g_abs_where(self):
        self.generic_test(
            "(a:{k:Integer where (k > 2)}) -> {v:Integer where (v > 1)}")

    def test_g_abs_where_2(self):
        self.generic_test("(a:Integer) -> {v:Integer where (v > 1)}")

    def assert_iet(self, ctx, e, x, T):
        NT = iet(ctx, e, x, T, 1)
        assert (is_subtype(ctx, NT, T))

    def test_iet(self):
        ctx = TypingContext()
        ctx.setup()

        T = ty("{v:Integer where (v == 1)}")
        self.assert_iet(ctx.with_var("x", T), expr.parse("1"), "x", T)

        T = ty("(v:{a:Integer where (a > 1)}) -> {k:Boolean where (k)}")
        self.assert_iet(ctx.with_var("x", ty("{x:Integer where (x==1)}")),
                        expr.parse("1"), "x", T)

    def test_complex(self):
        self.generic_test("D",
                          fun=se_app_in_context,
                          d=5,
                          extra_ctx=[("a", "(x:{ k : Integer | k > 3 }) -> A"),
                                     ("b", "(x:A) -> B"), ("c", "(x:B) -> C"),
                                     ("d", "(x:C) -> D"), ('A', 'type'),
                                     ('B', 'type'), ('C', 'type'),
                                     ('D', 'type')])


if __name__ == '__main__':
    unittest.main()
