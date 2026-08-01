from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.config import settings


def write_provisioned_scope(tmp_path: Path) -> Path:
    scope_file = tmp_path / "lab-scope.yaml"
    scope_file.write_text(
        yaml.dump(
            {
                "version": 1,
                "lab": {"name": "test-lab", "deploy_target": "local", "provisioned": True},
                "hosts": [
                    {
                        "id": "dc01",
                        "role": "domain_controller",
                        "hostname": "dc01.eadadl.lab",
                        "ip": "10.42.1.4",
                        "provisioned": True,
                    },
                ],
                "non_attackable_roles": ["attacker", "siem"],
            }
        )
    )
    return scope_file


# --- Safety: the real (unprovisioned) repo state refuses -------------------


def test_create_run_against_real_unprovisioned_scope_returns_403(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    # Deliberately does NOT monkeypatch settings.lab_scope_file — this
    # proves the API is gated by the actual repo state, the same way
    # `make attack` is (see .github/workflows/ci.yml's attack-runner smoke
    # test for the CLI equivalent of this check).
    response = client.post(
        "/runs", json={"scenario": "credential_harvest"}, headers=auth_headers
    )
    assert response.status_code == 403
    assert "domain_controller" in response.json()["detail"]


# --- Success path (monkeypatched provisioned scope) -------------------


def test_create_run_persists_and_returns_findings(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "lab_scope_file", write_provisioned_scope(tmp_path))

    response = client.post(
        "/runs", json={"scenario": "credential_harvest"}, headers=auth_headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["scenario"] == "credential_harvest"
    assert body["mode"] == "dry_run"
    assert len(body["findings"]) == 3
    assert body["findings"][0]["target_ip"] == "10.42.1.4"


def test_run_appears_in_history_and_is_individually_retrievable(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "lab_scope_file", write_provisioned_scope(tmp_path))
    create_response = client.post(
        "/runs", json={"scenario": "credential_harvest"}, headers=auth_headers
    )
    run_id = create_response.json()["id"]

    list_response = client.get("/runs", headers=auth_headers)
    assert list_response.status_code == 200
    assert any(r["id"] == run_id for r in list_response.json())

    detail_response = client.get(f"/runs/{run_id}", headers=auth_headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == run_id
    assert len(detail_response.json()["findings"]) == 3


def test_get_nonexistent_run_returns_404(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/runs/not-a-real-id", headers=auth_headers)
    assert response.status_code == 404


def test_create_run_with_unknown_scenario_returns_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post("/runs", json={"scenario": "nonexistent"}, headers=auth_headers)
    assert response.status_code == 404


# --- RBAC: viewer cannot trigger runs --------------------------------------


def test_viewer_cannot_create_run(client: TestClient, viewer_headers: dict[str, str]) -> None:
    response = client.post(
        "/runs", json={"scenario": "credential_harvest"}, headers=viewer_headers
    )
    assert response.status_code == 403


def test_viewer_can_list_runs(client: TestClient, viewer_headers: dict[str, str]) -> None:
    response = client.get("/runs", headers=viewer_headers)
    assert response.status_code == 200
