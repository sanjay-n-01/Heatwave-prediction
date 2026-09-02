from fastapi.testclient import TestClient

from main import app, create_alert_preview, get_risk


client = TestClient(app)


def test_required_risk_cases() -> None:
    assert get_risk(25, 25, False, False, False) == {
        "tier": "Safe",
        "score": 25,
    }
    assert get_risk(30, 25, False, False, False) == {
        "tier": "Caution",
        "score": 50,
    }
    assert get_risk(35, 65, True, False, False) == {
        "tier": "Extreme",
        "score": 100,
    }
    assert get_risk(39, 25, False, False, False) == {
        "tier": "Extreme",
        "score": 100,
    }
    assert get_risk(35, 30, False, False, True) == {
        "tier": "Extreme",
        "score": 100,
    }


def test_wbgt_boundaries() -> None:
    expected_tiers = {
        26.9: "Safe",
        27: "Caution",
        31.9: "Caution",
        32: "Danger",
        38: "Danger",
        38.1: "Extreme",
    }
    for wbgt, tier in expected_tiers.items():
        assert get_risk(wbgt, 25, False, False, False)["tier"] == tier


def test_risk_endpoint_and_validation() -> None:
    response = client.get(
        "/risk",
        params={
            "wbgt": 35,
            "age": 65,
            "has_cardio": "true",
            "has_respiratory": "false",
            "outdoor_labor": "false",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"tier": "Extreme", "score": 100}

    assert client.get(
        "/risk?wbgt=not-a-number&age=25&has_cardio=false"
        "&has_respiratory=false&outdoor_labor=false"
    ).status_code == 422
    assert client.get(
        "/risk?wbgt=30&age=-1&has_cardio=false"
        "&has_respiratory=false&outdoor_labor=false"
    ).status_code == 422


def test_alert_preview_endpoint() -> None:
    response = client.get(
        "/alert-preview",
        params={
            "wbgt": 35,
            "age": 65,
            "has_cardio": "true",
            "has_respiratory": "false",
            "outdoor_labor": "false",
        },
    )
    assert response.status_code == 200
    assert response.json() == create_alert_preview(12.9, 80.2, 35.0, "Extreme")
