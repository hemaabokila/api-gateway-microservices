from flask import request, current_app
from flask_restx import Namespace, Resource, fields

from . import db, message_queue_client
from .models import Product
from .schemas import product_schema, products_schema 

ns = Namespace('products', description='Product operations')

product_model = ns.model('Product', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a product'),
    'name': fields.String(required=True, description='The product\'s name'),
    'description': fields.String(description='The product\'s description'),
    'price': fields.Float(required=True, description='The product\'s price'),
    'stock_quantity': fields.Integer(required=True, description='Current stock quantity'),
    'is_available': fields.Boolean(description='Whether the product is currently available'),
    'created_at': fields.DateTime(readOnly=True, description='Timestamp of product creation'),
    'updated_at': fields.DateTime(readOnly=True, description='Timestamp of last update'),
})

product_update_model = ns.model('ProductUpdate', {
    'name': fields.String(description='The product\'s name'),
    'description': fields.String(description='The product\'s description'),
    'price': fields.Float(description='The product\'s price'),
    'stock_quantity': fields.Integer(description='Current stock quantity'),
    'is_available': fields.Boolean(description='Whether the product is currently available'),
})


def register_routes(app, api_instance):
    api_instance.add_namespace(ns)

    @ns.route('/<int:product_id>')
    @ns.param('product_id', 'The product unique identifier')
    class ProductResource(Resource):
        @ns.doc('get_product')
        @ns.marshal_with(product_model) 
        def get(self, product_id):
            """Fetch a product by ID"""
            product = Product.query.get(product_id)
            if product:
                return product_schema.dump(product), 200
            ns.abort(404, "Product not found")

        @ns.doc('update_product')
        @ns.expect(product_update_model)
        @ns.marshal_with(product_model)
        def put(self, product_id):
            """Update an existing product"""
            product = Product.query.get(product_id)
            if not product:
                ns.abort(404, "Product not found")
            
            data = request.get_json()
            if not data:
                ns.abort(400, "No data provided for update.")

            if 'name' in data:
                product.name = data['name']
            if 'description' in data:
                product.description = data['description']
            if 'price' in data:
                product.price = data['price']
            if 'stock_quantity' in data:
                product.stock_quantity = data['stock_quantity']
            if 'is_available' in data:
                product.is_available = data['is_available']

            db.session.commit()
            return product_schema.dump(product), 200

        @ns.doc('delete_product')
        @ns.response(204, 'Product deleted successfully')
        @ns.response(404, 'Product not found')
        def delete(self, product_id):
            """Delete a product"""
            product = Product.query.get(product_id)
            if not product:
                ns.abort(404, "Product not found")
            
            db.session.delete(product)
            db.session.commit()
            return '', 204

    @ns.route('/')
    class ProductList(Resource):
        @ns.doc('list_products')
        @ns.marshal_list_with(product_model)
        def get(self):
            """List all products"""
            products = Product.query.all()
            return products_schema.dump(products), 200

        @ns.doc('create_product')
        @ns.expect(product_model)
        @ns.marshal_with(product_model, code=201)
        def post(self):
            """Create a new product"""
            data = request.get_json()
            if not data or 'name' not in data or 'price' not in data or 'stock_quantity' not in data:
                ns.abort(400, "Missing 'name', 'price', or 'stock_quantity' in request body.")
            
            if Product.query.filter_by(name=data['name']).first():
                ns.abort(409, "Product name already exists.")

            new_product = Product(
                name=data['name'],
                description=data.get('description'),
                price=data['price'],
                stock_quantity=data['stock_quantity']
            )
            
            db.session.add(new_product)
            db.session.commit()
            if message_queue_client:
                event_data = {
                    "event_type": "create_product",
                    "product_id": new_product.id,
                    "name": new_product.name,
                    "price": new_product.price,
                    "timestamp": new_product.created_at.isoformat()
                }
                exchange_name = current_app.config.get('RABBITMQ_EVENTS_EXCHANGE')
                exchange_type = current_app.config.get('RABBITMQ_EVENTS_EXCHANGE_TYPE')
                routing_key = "product.created"
                message_queue_client.publish_event(exchange_name, routing_key, event_data, exchange_type)
            else:
                current_app.logger.warning("Message Queue Client not initialized. Product creation event not published.")

            return new_product, 201
