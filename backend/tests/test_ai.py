from app.ai.engine import calculate_quality_score, engine


def test_quality_grade_a():
    score, grade, status = calculate_quality_score(12.4, 0.6)
    assert grade == "A"
    assert status == "PASSED"
    assert score > 85


def test_isolation_forest_spike():
    r = engine.assess(
        temperature=89,
        humidity=65,
        delay_hours=31,
        distance_km=82,
        quality_score=60,
        quantity_kg=2500,
    )
    assert r.score >= 61
    assert r.level in {"HIGH", "CRITICAL"}
    assert any("Temperature" in x for x in r.reasons)
