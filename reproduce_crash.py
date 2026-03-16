from fastapi.testclient import TestClient
from app.main import create_app

app = create_app()
client = TestClient(app)

try:
    response = client.post(
        "/api/users",
        json={"user": {"username": "testuser", "email": "test@example.com", "password": "password"}}
    )
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    import traceback
    traceback.print_exc()
