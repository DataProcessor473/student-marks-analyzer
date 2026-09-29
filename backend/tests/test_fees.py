"""Fee management endpoint tests."""


def test_create_fee_structure(client, admin_headers):
    payload = {
        "class_name": "PYTEST-A",
        "fee_type": "Tuition",
        "amount": 5000.0,
        "frequency": "monthly",
        "academic_year": "2026-2027",
    }
    r = client.post("/fees/structure/create", json=payload, headers=admin_headers)
    assert r.status_code == 200
    assert "message" in r.json()


def test_list_fee_structures(client, admin_headers):
    r = client.get("/fees/structure", headers=admin_headers)
    assert r.status_code == 200
    assert "structures" in r.json()


def test_record_fee_payment(client, admin_headers):
    payload = {
        "student_id": 1,
        "fee_type": "Tuition",
        "amount": 5000.0,
        "payment_date": "2026-05-15",
        "payment_method": "cash",
        "status": "paid",
    }
    r = client.post("/fees/payment/create", json=payload, headers=admin_headers)
    assert r.status_code == 200


def test_list_fee_payments(client, admin_headers):
    r = client.get("/fees/payments", headers=admin_headers)
    assert r.status_code == 200
    assert "payments" in r.json()


def test_fee_reminders_list(client, admin_headers):
    r = client.get("/fees/reminders", headers=admin_headers)
    assert r.status_code == 200


def test_fee_reminders_preview(client, admin_headers):
    r = client.get("/fees/reminders/preview?days_ahead=7", headers=admin_headers)
    assert r.status_code == 200


def test_fees_unauthorized(client):
    r = client.get("/fees/structure")
    assert r.status_code == 401


def test_fee_payment_invalid_amount(client, admin_headers):
    payload = {
        "student_id": 1,
        "fee_type": "Tuition",
        "amount": -100.0,
        "payment_date": "2026-05-15",
    }
    r = client.post("/fees/payment/create", json=payload, headers=admin_headers)
    assert r.status_code == 422
