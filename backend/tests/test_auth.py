def test_register_success(client):
    response = client.post('/api/auth/register', json={
        'username': 'newuser',
        'email': 'new@test.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'User registered successfully'
    assert data['user']['username'] == 'newuser'

def test_register_duplicate_email(client, init_database):
    response = client.post('/api/auth/register', json={
        'username': 'anotheruser',
        'email': 'test@test.com', # Assuming test@test.com is seeded
        'password': 'password123'
    })
    assert response.status_code == 409
    assert response.get_json()['error'] == 'Email already registered'

def test_register_missing_fields(client):
    response = client.post('/api/auth/register', json={
        'username': 'missingemail',
        'password': 'password123'
    })
    assert response.status_code == 400

def test_login_success(client, init_database):
    response = client.post('/api/auth/login', json={
        'email': 'test@test.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert data['user']['username'] == 'testuser'

def test_login_invalid_password(client, init_database):
    response = client.post('/api/auth/login', json={
        'email': 'test@test.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert response.get_json()['error'] == 'Invalid email or password'

def test_login_nonexistent_user(client):
    response = client.post('/api/auth/login', json={
        'email': 'nobody@test.com',
        'password': 'password123'
    })
    assert response.status_code == 401

def test_me_endpoint_success(client, auth_headers):
    response = client.get('/api/auth/me', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['user']['username'] == 'testuser'

def test_me_endpoint_unauthorized(client):
    response = client.get('/api/auth/me')
    assert response.status_code == 401 # Missing Authorization Header
