from .test_client import client


def test_read_main():
    response = client.get("/test")
    print(response.json())
    assert response.status_code == 200
    assert response.json() == {"msg": "test"}

if __name__ == '__main__':
    test_read_main()
