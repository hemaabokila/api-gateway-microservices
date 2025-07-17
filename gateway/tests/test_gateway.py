import pytest
from ..app import create_app
from unittest.mock import patch, MagicMock
import os
import jwt
import time
import requests

@pytest.fixture
def client():
    os.environ['USERS_SERVICE_URL'] = 'http://mock_users_service:5001'
    os.environ['PRODUCTS_SERVICE_URL'] = 'http://mock_products_service:5002'
    os.environ['JWT_SECRET_KEY'] = 'test_super_secret_key_123'
    os.environ['FLASK_DEBUG'] = 'True' 
    os.environ['RATE_LIMIT_MAX_REQUESTS'] = '5'
    os.environ['RATE_LIMIT_WINDOW_SECONDS'] = '10'

    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def generate_jwt_token(user_id, secret_key, expires_in_seconds=3600):
    payload = {
        'user_id': user_id,
        'exp': time.time() + expires_in_seconds,
        'iat': time.time()
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

def test_health_check(client):
    rv = client.get('/health')
    assert rv.status_code == 200
    assert b"Gateway is healthy" in rv.data

@patch('requests.request')
def test_proxy_users_service(mock_requests_request, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"id": 1, "name": "Test User"}'
    mock_response.raw.headers = {'Content-Type': 'application/json'}
    mock_requests_request.return_value = mock_response

    rv = client.get('/api/users/1')

    mock_requests_request.assert_called_once_with(
        method='GET',
        url='http://mock_users_service:5001/1',
        headers=pytest.approx({'Accept': '*/*', 'User-Agent': 'werkzeug/3.0.3 python/3.9.19'}),
        data=b'',
        params={},
        allow_redirects=False
    )
    assert rv.status_code == 200
    assert b'{"id": 1, "name": "Test User"}' in rv.data

@patch('requests.request')
def test_proxy_service_unavailable(mock_requests_request, client):
    mock_requests_request.side_effect = requests.exceptions.ConnectionError

    rv = client.get('/api/users/1')
    assert rv.status_code == 503
    assert b"Service 'users' is unavailable" in rv.data

def test_auth_middleware_no_token(client):
    rv = client.get('/api/users/1')
    assert rv.status_code == 401
    assert b"Authorization header missing" in rv.data

@patch('requests.request')
def test_auth_middleware_valid_token(mock_requests_request, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"id": 1, "name": "Authenticated User"}'
    mock_response.raw.headers = {'Content-Type': 'application/json'}
    mock_requests_request.return_value = mock_response
    secret = os.environ['JWT_SECRET_KEY']
    token = generate_jwt_token(user_id=123, secret_key=secret)

    rv = client.get('/api/users/1', headers={'Authorization': f'Bearer {token}'})
    assert rv.status_code == 200
    assert b'Authenticated User' in rv.data
    mock_requests_request.assert_called_once()

def test_auth_middleware_invalid_token(client):
    rv = client.get('/api/users/1', headers={'Authorization': 'Bearer invalid_token'})
    assert rv.status_code == 401
    assert b"Invalid token" in rv.data

def test_rate_limiter_middleware(client):
    for i in range(5):
        rv = client.get('/api/health')
        assert rv.status_code == 200

    rv = client.get('/api/health')
    assert rv.status_code == 429
    assert b"Too many requests" in rv.data

