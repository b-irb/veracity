# SAT Solver

Simple SAT solver written in Python capable of parsing and solving propositional logic. This was an afternoon project, this is not intended for legitimate use.

## Demonstration

```py
import veracity
from pprint import pprint

def main() -> None:
    stmt = "P∨(Q∧R)∧(¬S∨(T∨¬U→V)∧W)"
    solutions = veracity.solve(stmt)
    pprint(solutions)

if __name__ == "__main__":
    main()
```

Running this prints

```
[{Variable(identifier='Q'): True,
  Variable(identifier='R'): True,
  Variable(identifier='W'): True},
 {Variable(identifier='Q'): True,
  Variable(identifier='R'): True,
  Variable(identifier='S'): False},
 {Variable(identifier='P'): True}]
```

We see there are 3 possible value assignments resulting in the expression evaluating to `T`.

## Build Instructions

```
$ git clone https://github.com/birb007/veracity.git
$ cd veracity
$ python setup.py install
```

You should now be able to import `veracity` from within Python.

## Grammar

```
var     = [a-Z]
expr    = [var] | [conjunction] | [disjunction] | [negation] | [implication] | ( [expr] )

conjunction = [expr] ∧ [expr]
disjunction = [expr] ∨ [expr]
negation    = ¬ [expr]
implication = [expr] → var
```

Expressions can be parenthesised to immediately evaluate prior to surrounding terms.

### Precedences

Negation > Conjunction > Disjunction > Implication

## Explanation

`P∧Q` will be parsed into `Conjunction(lhs=Variable(identifier="Q"), rhs=Variable(identifier="P"))` which is then solved by attempting to unify both sides with `T` by recursively resolving each nested term. If a contradiction is found (e.g. `P∧¬P` P cannot both be `T` and `F` so there are no solutions, however some constant expressions are removed with `veracity.simplify(expr)`). Disjunctions only require unification of one side which means two possible variable states are likely to result from a single disjunction.
