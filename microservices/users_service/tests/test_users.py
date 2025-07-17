import pytest
from microservices.users_service.app import create_app, db
from microservices.users_service.app.models import User
import json
import os

@pytest.fixture
def app():
    os.environ['FLASK_DEBUG'] = 'True'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:' 
    app = create_app()
    app.config['TESTING'] = True

    with app.app_context():
        db.create_all()
        user1 = User(username="testuser1", email="test1@example.com", password="password1")
        user2 = User(username="testuser2", email="test2@example.com", password="password2")
        db.session.add_all([user1, user2])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_user_success(client):
    """اختبار استرجاع مستخدم موجود."""
    rv = client.get('/users/1')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['username'] == "testuser1"
    assert data['email'] == "test1@example.com"
    assert 'password_hash' not in data

def test_get_user_not_found(client):
    """اختبار استرجاع مستخدم غير موجود."""
    rv = client.get('/users/999')
    assert rv.status_code == 404
    assert b"User not found" in rv.data

def test_create_user_success(client):
    """اختبار إنشاء مستخدم جديد بنجاح."""
    new_user_data = {"username": "newuser", "email": "new@example.com", "password": "newpassword"}
    rv = client.post('/users', json=new_user_data)
    assert rv.status_code == 201
    data = json.loads(rv.data)
    assert data['username'] == "newuser"
    assert data['email'] == "new@example.com"
    assert 'id' in data
    assert User.query.filter_by(username="newuser").first() is not None

def test_create_user_missing_data(client):
    """اختبار إنشاء مستخدم ببيانات ناقصة."""
    rv = client.post('/users', json={"username": "partial"})
    assert rv.status_code == 400
    assert b"Missing 'username', 'email', or 'password'" in rv.data

def test_create_user_duplicate_email(client):
    """اختبار إنشاء مستخدم ببريد إلكتروني مكرر."""
    duplicate_user_data = {"username": "anotheruser", "email": "test1@example.com", "password": "password"}
    rv = client.post('/users', json=duplicate_user_data)
    assert rv.status_code == 409
    assert b"Email already exists." in rv.data

def test_update_user_success(client):
    """اختبار تحديث مستخدم موجود."""
    update_data = {"email": "updated@example.com", "is_active": False}
    rv = client.put('/users/1', json=update_data)
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['email'] == "updated@example.com"
    assert data['is_active'] == False
    updated_user = User.query.get(1)
    assert updated_user.email == "updated@example.com"

def test_delete_user_success(client):
    """اختبار حذف مستخدم بنجاح."""
    rv = client.delete('/users/1')
    assert rv.status_code == 204
    assert User.query.get(1) is None

def test_get_all_users(client):
    """اختبار استرجاع جميع المستخدمين."""
    rv = client.get('/users')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data) == 2
    assert any(u['username'] == 'testuser1' for u in data)
    assert any(u['username'] == 'testuser2' for u in data)
