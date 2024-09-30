from flask import Blueprint, session

index_app = Blueprint('index', __name__)

@index_app.route('/')
def index():
    return {'status': 200}