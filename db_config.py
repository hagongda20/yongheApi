from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db_config(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/yonghe'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
