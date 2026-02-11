from ntt_parser import Gramma


def assert_machine(
    gramma: Gramma,
    start_non_terminal: str,
    terminals: list[str],
    non_terminals: list[str],
    productions: list[tuple[str, list[str], str | None]],
) -> None:
    assert gramma.StartNonTerminal == start_non_terminal
    _assert_2lists_equal_ignore_order(gramma.Terminals, terminals)
    _assert_2lists_equal_ignore_order(gramma.NonTerminals, non_terminals)

    for value, expect in zip(gramma.Productions, productions):
        assert (
            value[0] == expect[0]
        ), f"Expected left side {expect[0]} but found {value[0]}"
        assert (
            value[1] == expect[1]
        ), f"Expected right side {expect[1]} but found {value[1]}"
        if value[2] is None or expect[2] is None:
            assert (
                value[2] == expect[2]
            ), f"Expected return action {expect[2]} but found {value[2]}"
        else:
            assert value[2] is not None
            assert expect[2] is not None
            assert (
                value[2].strip() == expect[2].strip()
            ), f"Expected return action {expect[2]} but found {value[2]}"


def _assert_2lists_equal_ignore_order(list1: list[str], list2: list[str]) -> None:
    assert sorted(list1) == sorted(list2), f"{list1} != {list2}"


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
        productions=[("S", ["a", "b"], None)],
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
        productions=[("S", ["A", "b"], None), ("A", ["a"], None)],
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
        productions=[("S", ["A", "b"], None), ("S", ["acc"], None), ("A", ["a"], None)],
    )


def test_gramma_with_returns():
    gramma_str = """
    /start-gramma

    S: 
        A "b" { $$ = $1; }
        | "acc" { $$ = $1; }
        ;

    A:
        "a" { $$ = $1; }
        ;

    /end-gramma
"""

    gramma = Gramma.parse(gramma_str)

    assert_machine(
        gramma,
        "S",
        terminals=["a", "b", "acc"],
        non_terminals=["S", "A"],
        productions=[
            ("S", ["A", "b"], " $$ = $1; "),
            ("S", ["acc"], " $$ = $1; "),
            ("A", ["a"], " $$ = $1; "),
        ],
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
            ("Expr", ["Term", "+", "Expr"], None),
            ("Expr", ["Term"], None),
            ("Term", ["Factor", "*", "Term"], None),
            ("Term", ["Factor"], None),
            ("Factor", ["(", "Expr", ")"], None),
            ("Factor", ["num"], None),
        ],
    )


def test_parse_with_esp():
    gramma_str = """
    /start-gramma

    S:
        "a" A
        ;

    A: 
        "x"
        | ""
        ;

    /end-gramma
"""

    gramma = Gramma.parse(gramma_str)

    assert_machine(
        gramma,
        "S",
        terminals=["a", "x", ""],
        non_terminals=["S", "A"],
        productions=[
            ("S", ["a", "A"], None),
            ("A", ["x"], None),
            ("A", [""], None),
        ],
    )
