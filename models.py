from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Numeric, func
from datetime import datetime, date
from db_config import db

# 基类：自动添加时间戳字段
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 用户登录表
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    last_login_token = db.Column(db.String(255), nullable=True)
    last_login_time = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# 工人表（一个工人只能对应一个工序，可更换）
class Worker(db.Model, TimestampMixin):
    __tablename__ = 'workers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    id_card = db.Column(db.String(18), nullable=True)
    remark = db.Column(db.String(100))
    group = db.Column(db.String(40), nullable=True)  # 如 A组 / B组 

    entry_date = db.Column(db.Date, nullable=True, default=date.today)  # 入职时间，默认今天
    leave_date = db.Column(db.Date, nullable=True)  # 离职时间
    status = db.Column(db.String(10), nullable=True, default='在职')  # 状态：在职 / 离职

    process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=True)

    process = db.relationship('Process', back_populates='workers')
    wage_logs = db.relationship('WageLog', back_populates='worker')


# 工序表
class Process(db.Model, TimestampMixin):
    __tablename__ = 'processes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(100))

    workers = db.relationship('Worker', back_populates='process')
    spec_models = db.relationship('SpecModel', back_populates='process')
    wage_logs = db.relationship('WageLog', back_populates='process')
    #wage_prices = db.relationship('WagePrice', back_populates='process', cascade='all, delete-orphan')


# 规格型号表
class SpecModel(db.Model, TimestampMixin):
    __tablename__ = 'spec_models'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50))
    price = db.Column(Numeric(10, 2), nullable=False)

    process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False)
    process = db.relationship('Process', back_populates='spec_models')

    wage_logs = db.relationship('WageLog', back_populates='spec_model')

    def to_dict(self):
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
        }


# 工价表
'''
class WagePrice(db.Model, TimestampMixin):
    __tablename__ = 'wage_prices'
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(Numeric(10, 2), nullable=False)
    is_special = db.Column(db.Boolean, default=False)

    spec_model_id = db.Column(db.Integer, db.ForeignKey('spec_models.id'), nullable=False)
    spec_model = db.relationship('SpecModel', back_populates='wage_prices')

    # 新增：关联工序
    process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False)
    process = db.relationship('Process', back_populates='wage_prices')
'''

# 工资记录表
class WageLog(db.Model, TimestampMixin):
    __tablename__ = 'wage_logs'
    id = db.Column(db.Integer, primary_key=True)
    is_special = db.Column(db.Boolean, default=False)
    date = db.Column(db.Date, nullable=False)
    actual_price = db.Column(Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)  # 改为整数
    total_wage = db.Column(Numeric(10, 2), nullable=False)
    actual_group_size = db.Column(db.Integer, nullable=False, default=1)  # 新增字段，默认组人数为1,实际组人数
    remark = db.Column(db.String(100))

    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False)
    spec_model_id = db.Column(db.Integer, db.ForeignKey('spec_models.id'), nullable=False)

    worker = db.relationship('Worker', back_populates='wage_logs')
    process = db.relationship('Process', back_populates='wage_logs')
    spec_model = db.relationship('SpecModel', back_populates='wage_logs')
