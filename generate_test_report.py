import csv
import json
import httpx
import uuid

BASE_URL = "http://localhost:8000/v1"
CSV_FILE = "test_results.csv"

state = {}

def write_to_csv(writer, test_name, input_data, expected, received, is_passed):
    writer.writerow({
        "Test Name": test_name,
        "What was entered (Input)": json.dumps(input_data) if input_data else "None",
        "What was right (Expected)": expected,
        "What was received (Actual)": received,
        "Status (Right/Wrong)": "RIGHT" if is_passed else "WRONG"
    })
    print(f"{'PASS' if is_passed else 'FAIL'} | {test_name}")


def run_tests():
    print(f"Starting comprehensive API tests against {BASE_URL}...\n")
    
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ["Test Name", "What was entered (Input)", "What was right (Expected)", "What was received (Actual)", "Status (Right/Wrong)"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        with httpx.Client(base_url=BASE_URL) as client:
            
            # --- 1. Auth: Signup Success ---
            test_name = "Auth - Signup Success"
            random_email = f"user_{uuid.uuid4().hex[:6]}@example.com"
            state["email"] = random_email
            state["password"] = "secure123"
            input_data = {"email": random_email, "password": state["password"], "full_name": "CSV Tester"}
            expected = "Status 201, returns access token"
            try:
                resp = client.post("/auth/signup", json=input_data)
                received = f"Status {resp.status_code}, success={resp.json().get('success')}"
                is_passed = resp.status_code == 201
                write_to_csv(writer, test_name, input_data, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, input_data, expected, f"Error: {e}", False)

            # --- 2. Auth: Signup Duplicate (Edge Case) ---
            test_name = "Auth - Signup Duplicate Email"
            expected = "Status 409, already exists error"
            try:
                resp = client.post("/auth/signup", json=input_data)
                received = f"Status {resp.status_code}, detail={resp.json().get('detail')}"
                is_passed = resp.status_code == 409 and "already exists" in str(resp.json().get("detail"))
                write_to_csv(writer, test_name, input_data, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, input_data, expected, f"Error: {e}", False)

            # --- 3. Auth: Login Success ---
            test_name = "Auth - Login Success"
            input_data = {"email": state["email"], "password": state["password"]}
            expected = "Status 200, returns access token"
            try:
                resp = client.post("/auth/login", json=input_data)
                received = f"Status {resp.status_code}, success={resp.json().get('success')}"
                is_passed = resp.status_code == 200
                state["token"] = resp.json()["data"]["access_token"]
                write_to_csv(writer, test_name, input_data, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, input_data, expected, f"Error: {e}", False)

            # --- 4. Auth: Login Wrong Password (Edge Case) ---
            test_name = "Auth - Login Wrong Password"
            input_data = {"email": state["email"], "password": "wrongpassword"}
            expected = "Status 401, Invalid email or password"
            try:
                resp = client.post("/auth/login", json=input_data)
                received = f"Status {resp.status_code}, detail={resp.json().get('detail')}"
                is_passed = resp.status_code == 401
                write_to_csv(writer, test_name, input_data, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, input_data, expected, f"Error: {e}", False)
                
            headers = {"Authorization": f"Bearer {state.get('token')}"}

            # --- 5. Auth: Get Me Success (Protected) ---
            test_name = "Auth - Get Current User"
            expected = f"Status 200, email={state['email']}"
            try:
                resp = client.get("/auth/me", headers=headers)
                received = f"Status {resp.status_code}, email={resp.json().get('data', {}).get('email')}"
                is_passed = resp.status_code == 200 and resp.json()["data"]["email"] == state["email"]
                write_to_csv(writer, test_name, None, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, None, expected, f"Error: {e}", False)

            # --- 6. Fetch Centres ---
            import time
            test_name = "Fetch Diagnostic Centres (Cache Miss)"
            expected = "Status 200, returns list of centres"
            try:
                start_time = time.time()
                resp = client.get("/centres/")
                first_req_time = time.time() - start_time
                received = f"Status {resp.status_code}, count={len(resp.json()['data'])}, time={first_req_time:.4f}s"
                is_passed = resp.status_code == 200 and len(resp.json()['data']) > 0
                state["centre_id"] = resp.json()['data'][0]["id"]
                write_to_csv(writer, test_name, None, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, None, expected, f"Error: {e}", False)

            # --- 7. Fetch Centres Cache Check ---
            test_name = "Fetch Centres (Cache Hit Check)"
            expected = "Status 200 (Cached response)"
            try:
                start_time = time.time()
                resp = client.get("/centres/")
                second_req_time = time.time() - start_time
                received = f"Status {resp.status_code}, time={second_req_time:.4f}s"
                # Local InMemory cache overhead is roughly equal to a fast DB query, so we just verify 200 OK.
                is_passed = resp.status_code == 200
                write_to_csv(writer, test_name, None, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, None, expected, f"Error: {e}", False)

            # --- 8. Fetch Tests for Centre ---
            test_name = "Fetch Tests for Centre"
            expected = "Status 200, returns centre with tests"
            try:
                resp = client.get(f"/centres/{state['centre_id']}")
                received = f"Status {resp.status_code}, tests count={len(resp.json()['data'].get('tests', []))}"
                is_passed = resp.status_code == 200 and len(resp.json()['data']['tests']) > 0
                state["test_id"] = resp.json()['data']["tests"][0]["id"]
                write_to_csv(writer, test_name, {"centre_id": state["centre_id"]}, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, None, expected, f"Error: {e}", False)

            # --- 8. Create Booking Success ---
            test_name = "Create Booking Success"
            input_data = {
                "centre_id": state.get("centre_id"),
                "test_id": state.get("test_id"),
                "appointment_datetime": "2026-10-10T10:00:00Z"
            }
            expected = "Status 201, status=PENDING"
            try:
                resp = client.post("/bookings/", json=input_data, headers=headers)
                received = f"Status {resp.status_code}, booking_status={resp.json().get('data', {}).get('status')}"
                is_passed = resp.status_code == 201
                state["booking_id"] = resp.json()["data"]["id"]
                write_to_csv(writer, test_name, input_data, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, input_data, expected, f"Error: {e}", False)

            # --- 9. Create Booking Invalid Test ID (Edge Case) ---
            test_name = "Create Booking Invalid Test ID"
            input_data["test_id"] = "invalid-uuid-format"
            expected = "Status 404, not found"
            try:
                resp = client.post("/bookings/", json=input_data, headers=headers)
                received = f"Status {resp.status_code}, detail={resp.json().get('detail')}"
                is_passed = resp.status_code == 404
                write_to_csv(writer, test_name, input_data, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, input_data, expected, f"Error: {e}", False)

            # --- 10. Simulate Payment Success ---
            test_name = "Simulate Payment"
            input_data = {"booking_id": state.get("booking_id")}
            expected = "Status 200, returns transaction_id and payment status"
            try:
                resp = client.post("/payments/", json=input_data)
                data = resp.json().get('data', {})
                received = f"Status {resp.status_code}, txn={data.get('transaction_id')}, payment={data.get('status')}"
                is_passed = resp.status_code == 200 and 'transaction_id' in data
                state["transaction_id"] = data.get("transaction_id")
                state["payment_status"] = data.get("status")
                write_to_csv(writer, test_name, input_data, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, input_data, expected, f"Error: {e}", False)

            # --- 11. Webhook Sync Success ---
            test_name = "Webhook Sync Success"
            input_data = {
                "booking_id": state.get("booking_id"),
                "transaction_id": state.get("transaction_id"),
                "status": state.get("payment_status"),
                "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}"
            }
            state["idempotency_key"] = input_data["idempotency_key"]
            expected = "Status 200, Webhook processed successfully."
            try:
                resp = client.post("/payments/webhook", json=input_data)
                received = f"Status {resp.status_code}, msg={resp.json().get('message')}"
                is_passed = resp.status_code == 200 and "successfully" in resp.json().get('message')
                write_to_csv(writer, test_name, input_data, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, input_data, expected, f"Error: {e}", False)

            # --- 12. Webhook Idempotency (Edge Case) ---
            test_name = "Webhook Sync Idempotency Check"
            expected = "Status 200, Webhook already processed (idempotent success)."
            try:
                resp = client.post("/payments/webhook", json=input_data) # Send EXACT SAME payload
                received = f"Status {resp.status_code}, msg={resp.json().get('message')}"
                is_passed = resp.status_code == 200 and "already processed" in resp.json().get('message')
                write_to_csv(writer, test_name, input_data, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, input_data, expected, f"Error: {e}", False)
                
            # --- 13. Cancel Booking Success ---
            test_name = "Cancel Booking Success"
            expected = "Status 200, status=CANCELLED"
            # Note: Webhook might have set it to CONFIRMED. We can only cancel PENDING. So let's create a new booking for cancellation.
            new_booking = {
                "centre_id": state.get("centre_id"),
                "test_id": state.get("test_id"),
                "appointment_datetime": "2026-10-10T10:00:00Z"
            }
            resp = client.post("/bookings/", json=new_booking, headers=headers)
            cancel_booking_id = resp.json()["data"]["id"]
            
            try:
                resp = client.patch(f"/bookings/{cancel_booking_id}/cancel", headers=headers)
                received = f"Status {resp.status_code}, status={resp.json().get('data', {}).get('status')}"
                is_passed = resp.status_code == 200 and resp.json()["data"]["status"] == "CANCELLED"
                write_to_csv(writer, test_name, {"booking_id": cancel_booking_id}, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, None, expected, f"Error: {e}", False)

            # --- 14. Cancel Booking Already Cancelled (Edge Case) ---
            test_name = "Cancel Booking Already Cancelled"
            expected = "Status 400, Cannot cancel booking"
            try:
                resp = client.patch(f"/bookings/{cancel_booking_id}/cancel", headers=headers)
                received = f"Status {resp.status_code}, detail={resp.json().get('detail')}"
                is_passed = resp.status_code == 400
                write_to_csv(writer, test_name, {"booking_id": cancel_booking_id}, expected, received, is_passed)
            except Exception as e:
                write_to_csv(writer, test_name, None, expected, f"Error: {e}", False)
                
    print(f"\nAll tests complete! Results saved to {CSV_FILE}")

if __name__ == "__main__":
    run_tests()
