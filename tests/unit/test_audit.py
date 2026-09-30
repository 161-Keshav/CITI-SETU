from setu.audit import AuditLog


def test_hash_chain_detects_tampering(tmp_path) -> None:
    path = tmp_path / "audit.jsonl"
    audit = AuditLog(str(path))
    audit.append("score", {"tier": "warn"})
    audit.append("decision", {"tier": "hold"})
    assert audit.verify_chain()
    path.write_text(path.read_text().replace("warn", "allow"), encoding="utf-8")
    assert not audit.verify_chain()

