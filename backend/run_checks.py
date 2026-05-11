from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def login(email: str, password: str) -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    print(f"LOGIN {email}: {r.status_code}")
    if r.status_code != 200:
        print(r.text)
        raise SystemExit(1)
    token = r.json()["token"]
    return token


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def check_workers(token_admin: str, token_master: str) -> None:
    print("\n=== /workers/ as admin ===")
    r = client.get("/workers/", headers=auth_headers(token_admin))
    print("status:", r.status_code)
    print("count:", len(r.json()))

    print("\n=== /workers/ as master.moscow ===")
    r = client.get("/workers/", headers=auth_headers(token_master))
    print("status:", r.status_code)
    print("count:", len(r.json()))


def check_assign_worker(token_master: str) -> None:
    """
    Получаем первую заявку мастера и назначаем на неё первого работника.
    """
    print("\n=== assign worker to order ===")
    # список заявок мастера
    r = client.get("/orders/", headers=auth_headers(token_master))
    print("orders status:", r.status_code)
    orders = r.json()
    first_order = orders[0]
    order_id = first_order["id"]
    print("take order id:", order_id)

    # список работников
    r = client.get("/workers/", headers=auth_headers(token_master))
    workers = r.json()
    if not workers:
        print("no workers to assign")
        return
    worker_id = workers[0]["id"]
    print("assign worker id:", worker_id)

    r = client.patch(
        f"/orders/{order_id}",
        headers=auth_headers(token_master),
        json={"worker_id": worker_id},
    )
    print("patch status:", r.status_code)
    print("response worker_id:", r.json().get("worker", {}).get("id"))


def check_reports_removed(token_admin: str) -> None:
    print("\n=== /reports/personal should be 404 ===")
    r = client.get("/reports/personal", headers=auth_headers(token_admin))
    print("status:", r.status_code)


def main() -> None:
    token_admin = login("admin@autoservice.ru", "admin123")
    token_master = login("master.moscow@autoservice.ru", "master123")

    check_workers(token_admin, token_master)
    check_assign_worker(token_master)
    check_reports_removed(token_admin)


if __name__ == "__main__":
    main()

