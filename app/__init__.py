from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager
import cloudinary

app = Flask(__name__)


toan_connect_string = "mysql+pymysql://root:%s@localhost/toca_db?charset=utf8mb4" % quote("Huutoan123@")
canh_connect_string = "mysql+pymysql://root:%s@localhost/toca_db?charset=utf8mb4" % quote("Myca@1236")


app.config["SQLALCHEMY_DATABASE_URI"] = canh_connect_string
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config['SECRET_KEY'] = 'askrdghasdjfgakdsfuhgjhdsLGHU'

db = SQLAlchemy(app=app)
login = LoginManager(app=app)


cloudinary.config(
    cloud_name="dbd7vfk12",
    api_key="381798527745373",
    api_secret="mq7kD-ynrQsabeC3zUXc5zHuDIY"
)
# login = LoginManager(app=app)