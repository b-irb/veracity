import enum

from dataclasses import dataclass
from typing import Dict, List, Tuple, TypeVar, Union

Expr = TypeVar("Expr")


@dataclass
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
    ast = parser.parse()
    return ast
