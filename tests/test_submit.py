from submit import TOKEN_PATTERN


def test_team_code_pattern_accepts_production_card_code() -> None:
    assert TOKEN_PATTERN.fullmatch("MLG-BHJ3")


def test_team_code_pattern_accepts_demo_code() -> None:
    assert TOKEN_PATTERN.fullmatch("MLG-DEMO-DEMO-DEMO-DEMO")


def test_team_code_pattern_rejects_obsolete_long_code() -> None:
    assert not TOKEN_PATTERN.fullmatch("MLG-BHJ3-ABCD-2345-WXYZ")


def test_team_code_pattern_rejects_ambiguous_characters() -> None:
    assert not TOKEN_PATTERN.fullmatch("MLG-B0I1")
