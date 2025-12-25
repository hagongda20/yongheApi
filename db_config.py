from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db_config(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:12345678@localhost/yonghe'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dao-hao-shi-gou'
    db.init_app(app)
