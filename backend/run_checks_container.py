from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def login(email: str, password: str) -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    print(f"LOGIN {email}: {r.status_code}")
    if r.status_code != 200:
        print(r.text)
        raise SystemExit(1)
    return r.json()["token"]


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    admin_token = login("admin@autoservice.ru", "admin123")
    master_token = login("master.moscow@autoservice.ru", "master123")

    print("\\n=== GET /workers/ as admin ===")
    r = client.get("/workers/", headers=headers(admin_token))
    print("status:", r.status_code, "count:", len(r.json()))

    print("\\n=== GET /workers/ as master ===")
    r = client.get("/workers/", headers=headers(master_token))
    print("status:", r.status_code, "count:", len(r.json()))

    print("\\n=== PATCH /orders/{id} assign worker ===")
    r = client.get("/orders/", headers=headers(master_token))
    orders = r.json()
    if not orders:
        print("no orders for master")
    else:
        order_id = orders[0]["id"]
        r_workers = client.get("/workers/", headers=headers(master_token))
        workers = r_workers.json()
        if not workers:
            print("no workers to assign")
        else:
            wid = workers[0]["id"]
            r2 = client.patch(f"/orders/{order_id}", headers=headers(master_token), json={"worker_id": wid})
            print("patch status:", r2.status_code)
            print("order.worker.id:", r2.json().get("worker", {}).get("id"))

    print("\\n=== GET /reports/personal (should be 404) ===")
    r = client.get("/reports/personal", headers=headers(admin_token))
    print("status:", r.status_code)


if __name__ == "__main__":
    main()

