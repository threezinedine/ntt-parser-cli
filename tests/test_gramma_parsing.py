from ntt_parser import Gramma


def assert_machine(
    gramma: Gramma,
    start_non_terminal: str,
    terminals: list[str],
    non_terminals: list[str],
    productions: list[tuple[str, list[str]]],
) -> None:
    assert gramma.StartNonTerminal == start_non_terminal
    assert gramma.Terminals == list(set(terminals))
    assert gramma.NonTerminals == list(set(non_terminals))
    assert gramma.Productions == productions


def test_simple_1_product():
    gramma_str = """
    /start-gramma

    S: 
        "a" "b"
        ;

    /end-gramma
"""

    gramma = Gramma.parse(gramma_str)

    assert_machine(
        gramma,
        "S",
        terminals=["a", "b"],
        non_terminals=["S"],
        productions=[("S", ["a", "b"])],
    )


def test_gramma_with_non_terminal_in_production():
    gramma_str = """
    /start-gramma

    S: 
        A "b"
        ;

    A:
        "a"
        ;

    /end-gramma
"""

    gramma = Gramma.parse(gramma_str)

    assert_machine(
        gramma,
        "S",
        terminals=["a", "b"],
        non_terminals=["S", "A"],
        productions=[("S", ["A", "b"]), ("A", ["a"])],
    )


def test_gramma_with_multiple_productions():
    gramma_str = """
    /start-gramma

    S: 
        A "b"
        | "acc"
        ;

    A:
        "a"
        ;

    /end-gramma
"""

    gramma = Gramma.parse(gramma_str)

    assert_machine(
        gramma,
        "S",
        terminals=["a", "b", "acc"],
        non_terminals=["S", "A"],
        productions=[("S", ["A", "b"]), ("S", ["acc"]), ("A", ["a"])],
    )


def test_gramma_with_returns():
    gramma_str = """
    /start-gramma

    S: 
        A "b" { $$ = $1 }
        | "acc" { $$ = $1 }
        ;

    A:
        "a" { $$ = $1 }
        ;

    /end-gramma
"""

    gramma = Gramma.parse(gramma_str)

    assert_machine(
        gramma,
        "S",
        terminals=["a", "b", "acc"],
        non_terminals=["S", "A"],
        productions=[("S", ["A", "b"]), ("S", ["acc"]), ("A", ["a"])],
    )


def test_macro():
    gramma_str = """
    /start-macro

    TERM: Term

    /end-macro

    /start-gramma

    Expr:
         TERM "+" Expr
        | TERM 
        ;

    TERM:
        Factor "*" TERM 
        | Factor
        ;

    Factor:
        "(" Expr ")"
        | "num"
        ;

    /end-gramma
"""

    gramma = Gramma.parse(gramma_str)

    assert_machine(
        gramma,
        "Expr",
        terminals=["+", "*", "(", ")", "num"],
        non_terminals=["Expr", "Term", "Factor"],
        productions=[
            ("Expr", ["Term", "+", "Expr"]),
            ("Expr", ["Term"]),
            ("Term", ["Factor", "*", "Term"]),
            ("Term", ["Factor"]),
            ("Factor", ["(", "Expr", ")"]),
            ("Factor", ["num"]),
        ],
    )
