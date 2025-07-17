from flask import request, current_app
from flask_restx import Namespace, Resource, fields

from . import db, message_queue_client
from .models import User
from .schemas import user_schema, users_schema

ns = Namespace('users', description='User operations')

user_model = ns.model('User', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a user'),
    'username': fields.String(required=True, description='The user\'s username'),
    'email': fields.String(required=True, description='The user\'s email address'),
    'password': fields.String(required=True, writeOnly=True, description='The user\'s password'),
    'is_active': fields.Boolean(description='Whether the user account is active'),
    'is_admin': fields.Boolean(description='Whether the user has admin privileges'),
    'created_at': fields.DateTime(readOnly=True, description='Timestamp of user creation'),
    'updated_at': fields.DateTime(readOnly=True, description='Timestamp of last update'),
})

user_update_model = ns.model('UserUpdate', {
    'username': fields.String(description='The user\'s username'),
    'email': fields.String(description='The user\'s email address'),
    'password': fields.String(writeOnly=True, description='The user\'s new password'),
    'is_active': fields.Boolean(description='Whether the user account is active'),
    'is_admin': fields.Boolean(description='Whether the user has admin privileges'),
})


def register_routes(app, api_instance):
    api_instance.add_namespace(ns)

    @ns.route('/<int:user_id>')
    @ns.param('user_id', 'The user unique identifier')
    class UserResource(Resource):
        @ns.doc('get_user')
        @ns.marshal_with(user_model)
        def get(self, user_id):
            """Fetch a user by ID"""
            user = User.query.get(user_id)
            if user:
                return user_schema.dump(user), 200
            ns.abort(404, "User not found")

        @ns.doc('update_user')
        @ns.expect(user_update_model)
        @ns.marshal_with(user_model)
        def put(self, user_id):
            """Update an existing user"""
            user = User.query.get(user_id)
            if not user:
                ns.abort(404, "User not found")
            
            data = request.get_json()
            if not data:
                ns.abort(400, "No data provided for update.")

            if 'username' in data:
                user.username = data['username']
            if 'email' in data:
                user.email = data['email']
            if 'password' in data:
                user.set_password(data['password'])
            if 'is_active' in data:
                user.is_active = data['is_active']
            if 'is_admin' in data:
                user.is_admin = data['is_admin']

            db.session.commit()
            return user_schema.dump(user), 200

        @ns.doc('delete_user')
        @ns.response(204, 'User deleted successfully')
        @ns.response(404, 'User not found')
        def delete(self, user_id):
            """Delete a user"""
            user = User.query.get(user_id)
            if not user:
                ns.abort(404, "User not found")
            
            db.session.delete(user)
            db.session.commit()
            return '', 204

    @ns.route('/')
    class UserList(Resource):
        @ns.doc('list_users')
        @ns.marshal_list_with(user_model)
        def get(self):
            """List all users"""
            users = User.query.all()
            return users_schema.dump(users), 200

        @ns.doc('create_user')
        @ns.expect(user_model)
        @ns.marshal_with(user_model, code=201)
        def post(self):
            """Create a new user"""
            data = request.get_json()
            if not data or 'username' not in data or 'email' not in data or 'password' not in data:
                ns.abort(400, "Missing 'username', 'email', or 'password' in request body.")
            
            if User.query.filter_by(email=data['email']).first():
                ns.abort(409, "Email already exists.")
            if User.query.filter_by(username=data['username']).first():
                ns.abort(409, "Username already exists.")

            new_user = User(
                username=data['username'],
                email=data['email'],
                password=data['password']
            )
            
            db.session.add(new_user)
            db.session.commit()

            if message_queue_client:
                event_data = {
                    "event_type": "user_created",
                    "user_id": new_user.id,
                    "username": new_user.username,
                    "email": new_user.email,
                    "timestamp": new_user.created_at.isoformat()
                }
                exchange_name = current_app.config.get('RABBITMQ_EVENTS_EXCHANGE')
                exchange_type = current_app.config.get('RABBITMQ_EVENTS_EXCHANGE_TYPE')
                routing_key = "user.created"
                message_queue_client.publish_event(exchange_name, routing_key, event_data, exchange_type)
            else:
                current_app.logger.warning("Message Queue Client not initialized. User creation event not published.")

            return new_user, 201
