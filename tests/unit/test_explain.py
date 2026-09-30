from setu.explain import build_reasons


def test_reason_translation_is_limited_to_two() -> None:
    reasons = build_reasons([("FAN_IN_BURST", 0.5), ("UNSOLICITED_COLLECT", 0.4), ("FAST_PASS_THROUGH", 0.2)], "ta")
    assert len(reasons) == 2
    assert "பணம்" in reasons[0].text_localized
