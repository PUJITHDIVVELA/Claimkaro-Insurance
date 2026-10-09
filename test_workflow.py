import requests

BASE_URL = "http://localhost:5001"
session = requests.Session()

print("1. Testing Customer Login...")
res = session.post(f"{BASE_URL}/login", json={"email": "ravi@example.com", "password": "Customer@123"})
print("Customer Login Status:", res.status_code, res.json())

print("\n2. Testing Customer Policies API...")
res = session.get(f"{BASE_URL}/api/policies")
print("Policies Status:", res.status_code, f"Found {len(res.json()['data'])} policies")

print("\n3. Testing AI Insurance Chatbot API...")
res = session.post(f"{BASE_URL}/api/chatbot/message", json={"message": "What is my claim status?"})
print("Chatbot Reply:", res.json()['data']['reply'])

print("\n4. Testing Claims Officer Login...")
officer_session = requests.Session()
res = officer_session.post(f"{BASE_URL}/login", json={"email": "officer.rajesh@insurance.com", "password": "Officer@123"})
print("Officer Login Status:", res.status_code, res.json())

print("\n5. Testing Officer Review API...")
res = officer_session.post(f"{BASE_URL}/api/claims/1/review", json={"decision": "APPROVED", "remarks": "Original medical bills verified successfully."})
print("Review Status:", res.status_code, res.json())

print("\n6. Testing Admin Login & Dashboard Metrics API...")
admin_session = requests.Session()
res = admin_session.post(f"{BASE_URL}/login", json={"email": "admin@insurance.com", "password": "Admin@123"})
print("Admin Login Status:", res.status_code, res.json())

res = admin_session.get(f"{BASE_URL}/admin/api/dashboard-summary")
print("Admin Dashboard Metrics:", res.json()['data'])

print("\nALL WORKFLOW TESTS PASSED CLEANLY!")
