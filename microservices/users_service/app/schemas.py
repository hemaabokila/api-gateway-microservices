from .models import User
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        load_only = ("password",) 
        dump_only = ("id", "created_at", "updated_at") 
        include_relationships = True 

    password = fields.String(load_only=True)

user_schema = UserSchema()
users_schema = UserSchema(many=True)
