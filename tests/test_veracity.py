import unittest

from veracity import *


class TestParser(unittest.TestCase):
    def test_variable(self):
        parser = Parser("P")
        self.assertEqual(parser.parse(), Variable(identifier="P"))

    def test_negation(self):
        parser = Parser("¬P")
        self.assertEqual(parser.parse(), Negation(operand=Variable(identifier="P")))

    def test_conjunction(self):
        parser = Parser("P∧Q")
        self.assertEqual(
            parser.parse(),
            Conjunction(lhs=Variable(identifier="Q"), rhs=Variable(identifier="P")),
        )

    def test_disjunction(self):
        parser = Parser("P∨Q")
        self.assertEqual(
            parser.parse(),
            Disjunction(lhs=Variable(identifier="Q"), rhs=Variable(identifier="P")),
        )

    def test_implication(self):
        parser = Parser("P→Q")
        self.assertEqual(
            parser.parse(),
            Implication(
                conclusion=Variable(identifier="Q"), premise=Variable(identifier="P")
            ),
        )

    def test_nested_operators(self):
        parser = Parser("P∨Q∧R∧¬S")
        self.assertEqual(
            parser.parse(),
            Disjunction(
                lhs=Conjunction(
                    lhs=Conjunction(
                        lhs=Negation(operand=Variable(identifier="S")),
                        rhs=Variable(identifier="R"),
                    ),
                    rhs=Variable(identifier="Q"),
                ),
                rhs=Variable(identifier="P"),
            ),
        )

    def test_bad_char(self):
        parser = Parser("P ∨    \n¬ Q")
        self.assertEqual(
            parser.parse(),
            Disjunction(
                lhs=Negation(operand=Variable(identifier="Q")),
                rhs=Variable(identifier="P"),
            ),
        )


class TestSimplifier(unittest.TestCase):
    def test_simplify_const_conj(self):
        parser = Parser("P∧¬P")
        expr = veracity.simplify(parser.parse())
        self.assertEqual(expr, False)

    def test_simplify_const_disj(self):
        parser = Parser("(P∧¬P)∨Q")
        expr = veracity.simplify(parser.parse())
        self.assertEqual(expr, Variable(identifier="Q"))


class TestSolver(unittest.TestCase):
    def test_conjunction(self):
        expr = veracity.solve("V∧W")
        self.assertEqual(
            expr, [{Variable(identifier="W"): True, Variable(identifier="V"): True}]
        )

    def test_disjunction(self):
        expr = veracity.solve("P∨Q")
        self.assertEqual(
            expr, [{Variable(identifier="Q"): True}, {Variable(identifier="P"): True}]
        )

    def test_negation(self):
        expr = veracity.solve("¬V∧W")
        self.assertEqual(
            expr, [{Variable(identifier="W"): True, Variable(identifier="V"): False}]
        )

    def test_nested(self):
        expr = veracity.solve("P∨(Q∧R)∧(¬S∨(T∨¬U→V)∧W)")
        self.assertEqual(
            expr,
            [
                {
                    Variable(identifier="W"): True,
                    Variable(identifier="R"): True,
                    Variable(identifier="Q"): True,
                },
                {
                    Variable(identifier="S"): False,
                    Variable(identifier="R"): True,
                    Variable(identifier="Q"): True,
                },
                {Variable(identifier="P"): True},
            ],
        )

    def test_constant(self):
        expr = Conjunction(lhs=True, rhs=Variable(identifier="P"))
        cases = veracity.solve_expr(expr)
        self.assertEqual(cases, [{Variable(identifier="P"): True}])


def test_version():
    assert __version__ == "0.1.0"
