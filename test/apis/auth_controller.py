from test import client

access_token = ''
refresh_token = ''

def test_auth():
    payload = {'username': 'wwr', 'password': 'test password'}
    response = client.post('/auth', data=payload)
    print(response.json())
    global access_token, refresh_token
    access_token = response.json()['access_token']
    refresh_token = response.json()['refresh_token']
    assert response.status_code == 200
    return response.json()

def test_get_user():
    headers = {'Authorization': f'Bearer {access_token}',
               'refresh-token': refresh_token}
    response = client.get('/auth', headers=headers)
    print(response.json())
    assert response.status_code == 200

def run_all_test():
    test_auth()
    test_get_user()

if __name__ == '__main__':
    run_all_test()
