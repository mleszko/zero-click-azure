from __future__ import annotations

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_healthz_returns_ok() -> None:
    response = client.get('/healthz')

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'


def test_invoke_returns_trace_and_final_answer() -> None:
    response = client.post(
        '/invoke',
        json={
            'prompt': 'Describe security controls',
            'required_facts': [
                'Managed Identity is used for ACR pull',
                'AcrPull role assignment limits registry access',
            ],
            'max_correction_loops': 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload['attempts_used'] >= 1
    assert isinstance(payload['evaluation_history'], list)
    assert 'answer' in payload
