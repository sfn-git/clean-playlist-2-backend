from flask import Flask
from flask_cors import CORS
from routes.index import index_app
from routes.spotify import auth_app
from dotenv import load_dotenv
from secrets import token_hex
from flask_jwt_extended import JWTManager
import os

load_dotenv()
app = Flask(__name__)
app.register_blueprint(index_app, url_prefix='/')
app.register_blueprint(auth_app, url_prefix='/spotify')
jwt = JWTManager(app)

if os.getenv('ENV') == 'prod':
    app.config['JWT_SECRET_KEY'] = token_hex() #sessions will restart on app reset
    app.secret_key = token_hex() #sessions will restart on app reset
else:
    app.config['JWT_SECRET_KEY'] = "development" #session will stay
    app.secret_key = "development" #session will stay

CORS(app)


@app.errorhandler(404)
def page_not_found(error):
    d = {'status': 404, 'message': 'Resource not found.'}
    return d, 404

app.run(port=8080, host="0.0.0.0")