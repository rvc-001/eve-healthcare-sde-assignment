from decimal import Decimal
import pytest
from app.models.centre import DiagnosticCentre, DiagnosticTest
from app.models.booking import Booking


@pytest.fixture
def dummy_booking(db_session, auth_headers, client):
    """Seed a centre, test, and a valid booking via the API for payment testing."""
    centre = DiagnosticCentre(name="Payment Test Centre", location="Test City")
    db_session.add(centre)
    db_session.commit()
    db_session.refresh(centre)
    
    test = DiagnosticTest(
        centre_id=centre.id, 
        name="Payment Test", 
        price=Decimal("150.00")
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)

    # Create the booking via API
    resp = client.post("/v1/bookings/", headers=auth_headers, json={
        "centre_id": centre.id,
        "test_id": test.id,
        "appointment_datetime": "2026-10-10T10:00:00Z"
    })
    
    booking_id = resp.json()["data"]["id"]
    return db_session.query(Booking).filter(Booking.id == booking_id).first()


def test_simulate_payment(client, dummy_booking):
    """Test the mock payment gateway returns a valid response."""
    response = client.post("/v1/payments/", json={"booking_id": dummy_booking.id})
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["booking_id"] == dummy_booking.id
    assert "transaction_id" in data
    assert data["status"] in ["SUCCESS", "FAILED"]


def test_payment_webhook_idempotency(client, db_session, dummy_booking):
    """Test the webhook updates booking status and prevents double-processing (Phase 7)."""
    payload = {
        "booking_id": dummy_booking.id,
        "transaction_id": "txn_mock_123",
        "status": "SUCCESS",
        "idempotency_key": "idem-key-999"
    }
    
    # Call 1: Should succeed and update booking to CONFIRMED
    resp1 = client.post("/v1/payments/webhook", json=payload)
    assert resp1.status_code == 200
    assert resp1.json()["message"] == "Webhook processed successfully."
    
    # Check db
    db_session.refresh(dummy_booking)
    assert dummy_booking.status.value == "CONFIRMED"
    
    # Call 2: Identical payload should be caught by idempotency check
    resp2 = client.post("/v1/payments/webhook", json=payload)
    assert resp2.status_code == 200
    assert "idempotent success" in resp2.json()["message"]
