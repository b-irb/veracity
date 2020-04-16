import copy
import enum

from dataclasses import dataclass
from typing import Dict, List, Tuple, TypeVar, Union

Expr = TypeVar("Expr")


@dataclass(frozen=True)
class Variable:
    identifier: str


class Token(enum.Enum):
    CONJUNCTION = "∧"
    DISJUNCTION = "∨"
    IMPLICATION = "→"
    NEGATION = "¬"
    RIGHT_PAREN = ")"
    LEFT_PAREN = "("


@dataclass
class Conjunction:
    lhs: Expr
    rhs: Expr


@dataclass
class Disjunction:
    lhs: Expr
    rhs: Expr


@dataclass
class Implication:
    conclusion: Variable
    premise: Expr


@dataclass
class Negation:
    operand: Expr


@dataclass
class Parentheses:
    expr: Expr


Expr = Union[Variable, Conjunction, Disjunction, Implication, Negation, Expr]


class Parser:
    def __init__(self, proposition: str):
        self.proposition = proposition
        self.precedence = {
            Token.CONJUNCTION: 30,
            Token.DISJUNCTION: 20,
            Token.IMPLICATION: 10,
            Token.NEGATION: 40,
        }

    def parse(self) -> Expr:
        tokens = self.tokenise()
        return self._parse_internal(tokens)

    def tokenise(self) -> List[Token]:
        def predicate(char: str) -> bool:
            return char.isalpha() or char in set(token.value for token in Token)

        tokens = []
        for char in filter(predicate, self.proposition):
            try:
                token = Token(char)
            except ValueError:
                token = Variable(identifier=char)
            tokens.append(token)
        return tokens

    def _parse_internal(self, tokens: List[Token]) -> List[Token]:
        def peek(operators) -> Token:
            try:
                top = operators[-1]
            except IndexError:
                top = None
            return top

        handlers = {
            Token.CONJUNCTION: lambda v: Conjunction(v.pop(), v.pop()),
            Token.DISJUNCTION: lambda v: Disjunction(v.pop(), v.pop()),
            Token.IMPLICATION: lambda v: Implication(v.pop(), v.pop()),
            Token.NEGATION: lambda v: Negation(v.pop()),
        }
        operators = []
        values = []

        for token in tokens:
            if isinstance(token, Variable):
                values.append(token)
            elif token == Token.LEFT_PAREN:
                operators.append(token)
            elif token == Token.RIGHT_PAREN:
                while (top := peek(operators)) is not None and top != Token.LEFT_PAREN:
                    values.append(handlers[top](values))
                    operators.pop()
                operators.pop()
            else:
                while (
                    (top := peek(operators)) is not None
                    and top not in [Token.LEFT_PAREN, Token.RIGHT_PAREN]
                    and self.precedence[top] > self.precedence[token]
                ):
                    values.append(handlers[top](values))
                    operators.pop()
                operators.append(token)

        while (top := peek(operators)) is not None:
            values.append(handlers[top](values))
            operators.pop()

        return peek(values)


def solve(proposition: str) -> List[Dict[str, bool]]:
    parser = Parser(proposition)
    expr = parser.parse()
    if expr is None:
        return expr

    def f(expr: Expr, mappings: List[Dict[Variable, str]], constraint: bool):
        new_mappings = []
        for mapping in mappings:
            if isinstance(expr, Variable):
                if (val := mapping.get(expr, constraint)) != constraint:
                    continue
                mapping[expr] = constraint
                mapping = [mapping]

            elif isinstance(expr, Disjunction):
                mapping_copy = copy.deepcopy(mapping)
                new_mappings.extend(f(expr.lhs, [mapping_copy], constraint))
                mapping = f(expr.rhs, [mapping], constraint)

            elif isinstance(expr, Conjunction):
                m = f(expr.lhs, [mapping], constraint)
                mapping = f(expr.rhs, m, constraint)

            elif isinstance(expr, Negation):
                mapping = f(expr.operand, [mapping], not constraint)

            elif isinstance(expr, Implication):
                if constraint == False:
                    m = f(expr.premise, [mapping], True)
                    mapping = f(expr.conclusion, m, False)
                else:
                    mapping = [mapping]

            new_mappings.extend(mapping)
        return new_mappings

    simplified = simplify(expr)
    return f(expr, [{}], True)


def simplify(expr: Expr) -> Expr:
    mapping = {}

    def reduce_constexprs(expr: Expr, constraint: bool = True) -> bool:
        if isinstance(expr, Variable):
            val = mapping.get(expr, constraint)
            if val != constraint:
                return False
            mapping[expr] = constraint
        elif isinstance(expr, Negation):
            return reduce_constexprs(expr.operand, not constraint)
        elif isinstance(expr, Implication):
            return reduce_constexprs(expr.premise, constraint) and reduce_constexprs(
                expr.conclusion, constraint
            )
        elif isinstance(expr, Conjunction):
            return reduce_constexprs(expr.lhs, True) and reduce_constexprs(
                expr.rhs, True
            )
        elif isinstance(expr, Disjunction):
            expr.lhs = expr.lhs if (lhs := reduce_constexprs(expr.lhs)) else lhs
            expr.rhs = expr.rhs if (rhs := reduce_constexprs(expr.rhs)) else lhs
            if lhs == rhs == False:
                return False
        return True

    def rewrite(expr: Expr) -> bool:
        if isinstance(expr, Disjunction):
            if expr.lhs == expr.rhs == True:
                return expr
            return rewrite(expr.lhs if expr.lhs else expr.rhs)
        elif isinstance(expr, Conjunction):
            if expr.lhs == expr.rhs == True:
                return rewrite(expr)
            return False
        elif isinstance(expr, Implication):
            expr.premise = rewrite(expr.premise)
            expr.conclusion = rewrite(expr.conclusion)
        elif isinstance(expr, Negation):
            expr.operand = rewrite(expr.operand)
        return expr

    reduce_constexprs(expr)
    return rewrite(expr)

