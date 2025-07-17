import pytest
from microservices.products_service.app import create_app, db
from microservices.products_service.app.models import Product
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
        product1 = Product(name="Laptop Pro", price=1500.00, stock_quantity=10, description="High performance laptop")
        product2 = Product(name="Gaming Mouse", price=75.50, stock_quantity=50)
        db.session.add_all([product1, product2])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_product_success(client):
    rv = client.get('/products/1')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['name'] == "Laptop Pro"
    assert data['price'] == 1500.00

def test_get_product_not_found(client):
    rv = client.get('/products/999')
    assert rv.status_code == 404
    assert b"Product not found" in rv.data

def test_create_product_success(client):
    new_product_data = {"name": "Wireless Keyboard", "price": 80.00, "stock_quantity": 25}
    rv = client.post('/products', json=new_product_data)
    assert rv.status_code == 201
    data = json.loads(rv.data)
    assert data['name'] == "Wireless Keyboard"
    assert 'id' in data
    assert Product.query.filter_by(name="Wireless Keyboard").first() is not None

def test_create_product_missing_data(client):
    rv = client.post('/products', json={"name": "Partial Product"})
    assert rv.status_code == 400
    assert b"Missing 'name', 'price', or 'stock_quantity'" in rv.data

def test_create_product_duplicate_name(client):
    duplicate_product_data = {"name": "Laptop Pro", "price": 100.00, "stock_quantity": 5}
    rv = client.post('/products', json=duplicate_product_data)
    assert rv.status_code == 409
    assert b"Product name already exists." in rv.data

def test_update_product_success(client):
    update_data = {"price": 1450.00, "is_available": False}
    rv = client.put('/products/1', json=update_data)
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['price'] == 1450.00
    assert data['is_available'] == False
    updated_product = Product.query.get(1)
    assert updated_product.price == 1450.00

def test_delete_product_success(client):
    rv = client.delete('/products/1')
    assert rv.status_code == 204
    assert Product.query.get(1) is None

def test_get_all_products(client):
    rv = client.get('/products')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data) == 2
    assert any(p['name'] == 'Laptop Pro' for p in data)
    assert any(p['name'] == 'Gaming Mouse' for p in data)
