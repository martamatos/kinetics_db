from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import forms, routes_insert_data, routes_model_io, routes_modify_data, routes_see_data, routes_user
