from decimal import Decimal
import pytest
from datetime import datetime
from app.models.centre import DiagnosticCentre, DiagnosticTest, TestSlot


@pytest.fixture
def seed_centre_and_test(db_session):
    """Seed a centre and a test so we can make bookings against them."""
    centre = DiagnosticCentre(name="Test Centre", location="Test City")
    db_session.add(centre)
    db_session.commit()
    db_session.refresh(centre)
    
    test = DiagnosticTest(
        centre_id=centre.id, 
        name="Blood Test", 
        price=Decimal("150.00")
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)
    
    slot = TestSlot(
        test_id=test.id,
        start_time=datetime(2026, 10, 10, 10, 0, 0),
        end_time=datetime(2026, 10, 10, 10, 45, 0),
        is_booked=False
    )
    db_session.add(slot)
    db_session.commit()
    db_session.refresh(slot)
    
    return centre, test, slot


def test_create_booking_success(client, auth_headers, seed_centre_and_test):
    centre, test, slot = seed_centre_and_test
    
    response = client.post("/v1/bookings/", headers=auth_headers, json={
        "centre_id": centre.id,
        "test_id": test.id,
        "slot_id": slot.id
    })
    
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["status"] == "PENDING"
    assert float(data["amount"]) == 150.0


def test_create_booking_invalid_test(client, auth_headers, seed_centre_and_test):
    centre, _, slot = seed_centre_and_test
    
    response = client.post("/v1/bookings/", headers=auth_headers, json={
        "centre_id": centre.id,
        "test_id": "invalid-uuid",
        "slot_id": slot.id
    })
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_cancel_booking(client, auth_headers, seed_centre_and_test):
    centre, test, slot = seed_centre_and_test
    
    # Create booking
    create_resp = client.post("/v1/bookings/", headers=auth_headers, json={
        "centre_id": centre.id,
        "test_id": test.id,
        "slot_id": slot.id
    })
    booking_id = create_resp.json()["data"]["id"]
    
    # Cancel it
    cancel_resp = client.patch(f"/v1/bookings/{booking_id}/cancel", headers=auth_headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["data"]["status"] == "CANCELLED"
    
    # Try cancelling again (edge case)
    cancel_again = client.patch(f"/v1/bookings/{booking_id}/cancel", headers=auth_headers)
    assert cancel_again.status_code == 400
    assert "Cannot cancel booking with status CANCELLED" in cancel_again.json()["detail"]
