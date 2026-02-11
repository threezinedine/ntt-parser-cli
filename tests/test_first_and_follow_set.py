import pytest  # type: ignore
from ntt_parser import Gramma


def assert_first_set_machine(
    gramma: Gramma,
    expected_first_set: list[tuple[str, set[str]]],
):
    first_set = sorted(gramma.FirstSet, key=lambda x: x[0])
    expected_first_set = sorted(expected_first_set, key=lambda x: x[0])

    for (nt1, fs1), (nt2, fs2) in zip(first_set, expected_first_set):
        assert nt1 == nt2, f"Expected NonTerminal {nt2} but found {nt1}"
        assert sorted(list(fs1)) == sorted(
            list(fs2)
        ), f"Expected FirstSet {sorted(list(fs2))} but found {sorted(list(fs1))}"


def test_validate_valid_gramma():
    gramma_str = """
    /start-gramma

    S: 
        "a" "b"
        ;

    /end-gramma
"""
    gramma = Gramma.parse(gramma_str)
    gramma.validate()  # Should not raise any exception


def test_validate_invalid_gramma():
    gramma_str = """
    /start-gramma

    S: 
        A "b"
        ;

    /end-gramma
"""
    gramma = Gramma.parse(gramma_str)
    try:
        gramma.validate()
        assert False, "Expected ValueError for undefined symbol 'A'"
    except ValueError as e:
        assert str(e) == "Symbol 'A' is not defined in the gramma"


def test_create_first_and_follow_sets():
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

    gramma.parse_first_set()

    assert_first_set_machine(
        gramma,
        [
            ("S", {"a", "acc"}),
            ("A", {"a"}),
        ],
    )


def test_first_set_with_epsilon_production():
    gramma_str = """
    /start-gramma

    S: 
        A "b"
        | "acc"
        ;

    A:
        ""
        | "a"
        ;

    /end-gramma
"""

    gramma = Gramma.parse(gramma_str)

    gramma.parse_first_set()

    assert_first_set_machine(
        gramma,
        [
            ("S", {"", "a", "b", "acc"}),
            ("A", {"", "a"}),
        ],
    )


def test_first_set_for_complex_case():
    gramma_str = """
    /start-gramma

    E: T E';

    E': "+" T E'
        | ""
        ;

    T: F T';

    T': "*" F T'
        | ""
        ;

    F: "(" E ")"
        | "0"
        ;


    /end-gramma
"""

    gramma = Gramma.parse(gramma_str)

    gramma.parse_first_set()

    assert_first_set_machine(
        gramma,
        [
            ("E", {"(", "0"}),
            ("E'", {"+", ""}),
            ("T", {"(", "0"}),
            ("T'", {"*", ""}),
            ("F", {"(", "0"}),
        ],
    )
