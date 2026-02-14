import pytest  # type: ignore
from ntt_parser import Gramma


def assert_set_machine(
    set: list[tuple[str, list[str]]],
    expected_set: list[tuple[str, set[str]]],
):
    first_set = sorted(set, key=lambda x: x[0])
    expected_set = sorted(expected_set, key=lambda x: x[0])

    assert len(set) == len(
        expected_set
    ), f"Expected set length {len(expected_set)} but found {len(set)}"
    for index, ((nt1, fs1), (nt2, fs2)) in enumerate(zip(first_set, expected_set)):
        assert nt1 == nt2, f"Expected NonTerminal {nt2} but found {nt1}"
        assert sorted(list(fs1)) == sorted(
            list(fs2)
        ), f"Expected Set {sorted(list(fs2))} but found {sorted(list(fs1))} at non-terminal {nt1} (index {index})"


def assert_first_set_machine(
    gramma: Gramma,
    expected_first_set: list[tuple[str, set[str]]],
):
    assert_set_machine(gramma.FirstSet, expected_first_set)


def assert_follow_set_machine(
    gramma: Gramma,
    expected_follow_set: list[tuple[str, set[str]]],
):
    assert_set_machine(gramma.FollowSet, expected_follow_set)


def test_validate_valid_gramma():
    gramma_str = """
    /start-gramma

    S: 
        "a" "b"
        ;

    /end-gramma
"""

    Gramma.parse(gramma_str)  # Should not raise any exception


def test_validate_invalid_gramma():
    gramma_str = """
    /start-gramma

    S: 
        A "b"
        ;

    /end-gramma
"""
    # raise assertion error because A is not defined
    with pytest.raises(AssertionError):
        Gramma.parse(gramma_str)


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

    assert_first_set_machine(
        gramma,
        [
            ("S", {'"a"', '"acc"'}),
            ("A", {'"a"'}),
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

    assert_first_set_machine(
        gramma,
        [
            ("S", {'""', '"a"', '"acc"'}),
            ("A", {'""', '"a"'}),
        ],
    )


def test_first_set_for_complex_case():
    gramma_str = """
    /start-lexma

    number: /[0-9]+/

    /end-lexma

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
        | number
        ;


    /end-gramma
"""

    gramma = Gramma.parse(gramma_str)

    assert_first_set_machine(
        gramma,
        [
            ("E", {'"("', "number"}),
            ("E'", {'"+"', '""'}),
            ("T", {'"("', "number"}),
            ("T'", {'"*"', '""'}),
            ("F", {'"("', "number"}),
        ],
    )

    gramma.parse_follow_set()

    assert_follow_set_machine(
        gramma,
        [
            ("E", {'")"', "$"}),
            ("E'", {'")"', "$"}),
            ("T", {'"+"', '")"', "$"}),
            ("T'", {'"+"', '")"', "$"}),
            ("F", {'"*"', '"+"', '")"', "$"}),
        ],
    )
