from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_scenarios_returns_both_chains(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/scenarios", headers=auth_headers)
    assert response.status_code == 200
    ids = {s["id"] for s in response.json()}
    assert ids == {"credential_harvest", "domain_dominance"}


def test_scenario_summary_includes_technique_ids(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/scenarios", headers=auth_headers)
    by_id = {s["id"]: s for s in response.json()}
    assert by_id["credential_harvest"]["technique_ids"] == [
        "bloodhound_collect",
        "kerberoasting",
        "asrep_roasting",
    ]
