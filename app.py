from flask import Flask
from flask_cors import CORS
from routes.index import index_app
from routes.spotify import auth_app
from dotenv import load_dotenv
from secrets import token_hex
from flask_session import Session #https://flask-session.readthedocs.io/en/latest/introduction.html
from cachelib.file import FileSystemCache
import os
import shutil

# Handles sessions directory
dir_path="./sessions"
if os.path.exists(dir_path):
    shutil.rmtree(dir_path)

os.makedirs(dir_path)

load_dotenv()
app = Flask(__name__)
app.register_blueprint(index_app, url_prefix='/')
app.register_blueprint(auth_app, url_prefix='/spotify')

SESSION_TYPE = 'cachelib'
SESSION_COOKIE_DOMAIN = os.getenv('APP_BASE_DOMAIN')
SESSION_CACHELIB = FileSystemCache(threshold=500, cache_dir="./sessions")
SESSION_USE_SIGNER = True
app.config.from_object(__name__)

if os.getenv('ENV') == 'prod':
    SESSION_COOKIE_SECURE = True
    app.secret_key = token_hex() #sessions will restart on app reset
else:
    app.secret_key = "development" #session will stay on app reset

Session(app)
CORS(app)

@app.errorhandler(404)
def page_not_found(error):
    d = {'status': 404, 'message': 'Resource not found.'}
    return d, 404

app.run(port=8080, host="0.0.0.0")