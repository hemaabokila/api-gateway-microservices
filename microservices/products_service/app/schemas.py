from .models import Product
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields

class ProductSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        load_instance = True
        dump_only = ("id", "created_at", "updated_at")
    price = fields.Float(required=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
