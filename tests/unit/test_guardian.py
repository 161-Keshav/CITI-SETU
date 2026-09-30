from setu.guardian import GuardianService, HoldState


def test_guardian_link_is_single_use() -> None:
    service = GuardianService("secret", 10)
    service.enroll("asha@bankA", "Arun")
    hold, token = service.create("asha@bankA", "mule@bankC", 24500, "Check")
    completed = service.decision(hold.id, token, "reject")
    assert completed.state == HoldState.CANCELLED
    try:
        service.decision(hold.id, token, "approve")
    except ValueError:
        pass
    else:
        raise AssertionError("replayed guardian link must fail")


def test_payer_can_cancel_pending_hold() -> None:
    service = GuardianService("secret", 10)
    hold, _ = service.create("asha@bankA", "mule@bankC", 24500, "Check")
    assert service.cancel(hold.id).state == HoldState.CANCELLED

