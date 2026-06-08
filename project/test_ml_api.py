import requests

from config import API_URL

HEALTH_URL = "http://localhost:8001/health"


def test_health():
    print("Checking /health endpoint...")

    response = requests.get(
        HEALTH_URL,
        timeout=5,
    )

    print("Status code:", response.status_code)
    print("Response:", response.json())

    response.raise_for_status()


def test_low_risk_case():
    print("\nChecking low-risk inventory case...")

    payload = {
        "current_stock": 35,
        "shelf_capacity": 50,
        "sales_last_10min": 2,
        "stock_ratio": 0.7,
        "replenishment_pending": 0,
        "category_encoded": 0,
        "store_encoded": 0,
    }

    response = requests.post(
        API_URL,
        json=payload,
        timeout=5,
    )

    print("Status code:", response.status_code)
    print("Payload:", payload)
    print("Response:", response.json())

    response.raise_for_status()


def test_high_risk_case():
    print("\nChecking high-risk inventory case...")

    payload = {
        "current_stock": 4,
        "shelf_capacity": 40,
        "sales_last_10min": 14,
        "stock_ratio": 0.1,
        "replenishment_pending": 0,
        "category_encoded": 0,
        "store_encoded": 0,
    }

    response = requests.post(
        API_URL,
        json=payload,
        timeout=5,
    )

    print("Status code:", response.status_code)
    print("Payload:", payload)
    print("Response:", response.json())

    response.raise_for_status()


def main():
    test_health()
    test_low_risk_case()
    test_high_risk_case()

    print("\nAPI test completed.")


if __name__ == "__main__":
    main()