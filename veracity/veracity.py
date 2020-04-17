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
    """Parser to transform propositional logic statements to IR.

    Args:
        proposition: Propositional logic expression.
    """

    def __init__(self, proposition: str):
        self.proposition = proposition
        self.precedence = {
            Token.CONJUNCTION: 30,
            Token.DISJUNCTION: 20,
            Token.IMPLICATION: 10,
            Token.NEGATION: 40,
        }

    def parse(self) -> Expr:
        """Transform proposition into IR.

        The proposition is tokenised then parsed. Invalid characters are
        ignored.

        Returns:
            Representation of propositional logic (evaluated in RPN form).
        """
        tokens = self.tokenise()
        return self._parse_internal(tokens)

    def tokenise(self) -> List[Token]:
        """Tokenise proposition.

        Interpret each valid char as a token and ignore invalid chars.

        Returns:
            Valid tokens found within proposition.
        """

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

    def _parse_internal(self, tokens: List[Token]) -> Expr:
        """Parse tokens into IR.

        Tokens are parsed using shunting-yard into an RPN form then combined
        to represent fully formed expressions.

        Args:
            tokens: List of tokens to parse sequentially.

        Returns:
            Representation of parsed tokens.
        """

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


def solve(proposition: str) -> List[Dict[Variable, bool]]:
    """Find all solutions for given proposition.

    Attempt to find solutions for the proposition after parsing and
    simplification.

    Args:
        proposition: Propositional logic statement.

    Returns:
        List of possible variable mappings for the given proposition to
        evaluate to T.

    Examples:
        >>> solve("(P∧¬P)∨Q")
        [{Variable(identifier='Q'): True}]
    """
    parser = Parser(proposition)
    expr = parser.parse()
    if expr is None:
        return expr

    simplified = simplify(expr)
    return _solve_expr(expr, [{}], True)


def solve_expr(expr: Expr) -> List[Dict[Variable, bool]]:
    """Find all solutions for given IR expression.

    Args:
        expr: Expression to solve.

    Returns:
        List of possible variable mappings for the given expression to
        evaluate to T.
    """
    return _solve_expr(expr, [{}], True)


def _solve_expr(
    expr: Expr, mappings: List[Dict[Variable, str]], constraint: bool
) -> List[Dict[Variable, bool]]:
    """Determine all evaluation trees to evaluate to desired constraint.

    For each initial variable mapping we attempt to coerce the current
    expression into the given constraint. If the expression is a variable
    which we have already assigned a different value to what is required,
    we reject the variable mapping. Otherwise, we denote the value of the
    variable in the current mapping.

    Conjunction requires both operands to evaluate to the same outcome. We
    attempt to coerce both sides, if this is impossible we reject the current
    variable mapping.

    Disjunction only requires one operand to evaluate to the constraint.
    Consequently, there are potentially two possible variable mappings per
    disjunction (with each mapping a different state where the expression
    holds). These cases stack, for `n` nested disjunctions, there will be
    `2^(n-1)` mappings. A copy of the current mapping is created so both
    operands are given a unique context. We reject the mapping of an operand
    if it fails to coerce.

    Negation requires its operand to evaluate to the opposite of the current
    constraint. If this is impossible, we reject the mapping.

    Implication attempts to satisfy the truth table.

    ===== ===== =====
      P     Q    P→Q
    ===== ===== =====
      T     T     T
      T     F     F
      F     T     T
      F     F     T
    ===== ===== =====

    Args:
        expr: Expression to solve.
        mappings: List of variable mappings.
        constraint: Target value for expression to evaluate to.

    Returns:
        List of possible variable mappings for dependent expressions to evaluate
        to `constraint`.
    """
    new_mappings = []
    for mapping in mappings:
        if isinstance(expr, Variable):
            if (val := mapping.get(expr, constraint)) != constraint:
                continue
            mapping[expr] = constraint
            mapping = [mapping]

        elif isinstance(expr, Disjunction):
            mapping_copy = copy.deepcopy(mapping)
            new_mappings.extend(_solve_expr(expr.lhs, [mapping_copy], constraint))
            mapping = _solve_expr(expr.rhs, [mapping], constraint)

        elif isinstance(expr, Conjunction):
            m = _solve_expr(expr.lhs, [mapping], constraint)
            mapping = _solve_expr(expr.rhs, m, constraint)

        elif isinstance(expr, Negation):
            mapping = _solve_expr(expr.operand, [mapping], not constraint)

        elif isinstance(expr, Implication):
            if constraint == False:
                m = _solve_expr(expr.premise, [mapping], True)
                mapping = _solve_expr(expr.conclusion, m, False)
            else:
                mapping = [mapping]

        new_mappings.extend(mapping)
    return new_mappings


def simplify(expr: Expr) -> Expr:
    """Remove constant expressions from expr.

    Attempt to satisfy constraint for each expression. By determining required
    values for an expression to hold we can determine expressions with constant
    results (e.g. P∧¬P is always F).

    Args:
        expr: Expression to simplify.

    Examples:
        >>> expr = Parser("(P∧¬P)∨Q").parse()
        >>> simplify(expr)
         Variable(identifier='Q')
    """
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


def stringify(expr: Expr) -> str:
    """Transform IR into string.

    Args:
        expr: Expression to transform.

    Returns:
        String representation of expression.
    """
    if isinstance(expr, Variable):
        return expr.identifier
    if isinstance(expr, Negation):
        return f"({Token.NEGATION.value}{stringify(expr.operand)})"
    if isinstance(expr, Conjunction):
        return (
            f"({stringify(expr.lhs)} {Token.CONJUNCTION.value} {stringify(expr.rhs)})"
        )
    if isinstance(expr, Disjunction):
        return (
            f"({stringify(expr.lhs)} {Token.DISJUNCTION.value} {stringify(expr.rhs)})"
        )
    if isinstance(expr, Implication):
        return f"({stringify(expr.premise)} {Token.IMPLICATION.value} {stringify(expr.conclusion)})"
