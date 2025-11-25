from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Numeric
from datetime import datetime, date
from db_config import db

# 基类：自动添加时间戳字段
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def to_dict(self, exclude=None, relations=None):
        if exclude is None:
            exclude = []
        if relations is None:
            relations = []

        data = {}
        # 基本字段
        for key, value in self.__dict__.items():
            if not key.startswith('_') and key not in exclude:
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                elif hasattr(value, 'to_dict'):
                    data[key] = value.to_dict()
                else:
                    data[key] = value

        # 关系字段
        for rel in relations:
            if hasattr(self, rel):
                rel_obj = getattr(self, rel)
                if rel_obj is None:
                    data[rel] = None
                elif isinstance(rel_obj, list):
                    data[rel] = [item.to_dict() for item in rel_obj if hasattr(item, 'to_dict')]
                elif hasattr(rel_obj, 'to_dict'):
                    data[rel] = rel_obj.to_dict()

        return data

# 用户登录表
class User(db.Model, TimestampMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, comment="用户ID")
    username = db.Column(db.String(50), unique=True, nullable=False, comment="登录用户名")
    password_hash = db.Column(db.String(128), nullable=False, comment="密码哈希值")
    last_login_token = db.Column(db.String(255), comment="上次登录的Token")
    last_login_time = db.Column(db.DateTime, default=datetime.utcnow, comment="上次登录时间")
    role = db.Column(db.String(20), nullable=False, default='user', comment="角色：admin/user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# 工人表
class Worker(db.Model, TimestampMixin):
    __tablename__ = 'workers'
    id = db.Column(db.Integer, primary_key=True, comment="工人ID")
    name = db.Column(db.String(50), nullable=False, comment="工人姓名")
    id_card = db.Column(db.String(18), unique=True, comment="身份证号")
    group = db.Column(db.String(40), comment="班组，如 A组 / B组")
    entry_date = db.Column(db.Date, default=date.today, comment="入职日期")
    leave_date = db.Column(db.Date, comment="离职日期")
    status = db.Column(db.String(10), nullable=False, default='在职', comment="状态：在职 / 离职")
    remark = db.Column(db.Text, comment="备注")

    process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), comment="当前所属工序ID")
    process = db.relationship('Process', back_populates='workers')
    wage_logs = db.relationship('WageLog', back_populates='worker', cascade='all, delete-orphan')

# 工序表
class Process(db.Model, TimestampMixin):
    __tablename__ = 'processes'
    id = db.Column(db.Integer, primary_key=True, comment="工序ID")
    name = db.Column(db.String(50), unique=True, nullable=False, comment="工序名称，如 '冲压'")
    description = db.Column(db.String(200), comment="工序描述")

    workers = db.relationship('Worker', back_populates='process')
    spec_models = db.relationship('SpecModel', back_populates='process', cascade='all, delete-orphan')
    wage_logs = db.relationship('WageLog', back_populates='process')
    # wage_prices = db.relationship('WagePrice', back_populates='process', cascade='all, delete-orphan')

# 规格型号表
class SpecModel(db.Model, TimestampMixin):
    __tablename__ = 'spec_models'
    id = db.Column(db.Integer, primary_key=True, comment="规格型号ID")
    name = db.Column(db.String(50), nullable=False, comment="规格型号名称，如 'M20螺母'")
    category = db.Column(db.String(50), comment="产品分类")
    price = db.Column(Numeric(10, 2), nullable=False, comment="价格（元）")

    process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False, comment="所属工序ID")
    process = db.relationship('Process', back_populates='spec_models')
    wage_logs = db.relationship('WageLog', back_populates='spec_model', cascade='all, delete-orphan')
    # wage_prices = db.relationship('WagePrice', back_populates='spec_model', cascade='all, delete-orphan')

# 工价表
# class WagePrice(db.Model, TimestampMixin):
#     __tablename__ = 'wage_prices'
#     id = db.Column(db.Integer, primary_key=True, comment="工价ID")
#     price = db.Column(Numeric(10, 2), nullable=False, comment="工价（元/件）")
#     is_special = db.Column(db.Boolean, default=False, comment="是否为特殊工价（如赶工、返工）")
#     effective_date = db.Column(db.Date, default=date.today, comment="工价生效日期")
#
#     spec_model_id = db.Column(db.Integer, db.ForeignKey('spec_models.id'), nullable=False, comment="关联的规格型号ID")
#     spec_model = db.relationship('SpecModel', back_populates='wage_prices')
#
#     process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False, comment="关联的工序ID")
#     process = db.relationship('Process', back_populates='wage_prices')

# 工资记录表
class WageLog(db.Model, TimestampMixin):
    __tablename__ = 'wage_logs'
    id = db.Column(db.Integer, primary_key=True, comment="工资记录ID")
    date = db.Column(db.Date, nullable=False, comment="记录日期")
    actual_price = db.Column(db.Numeric(10, 2), nullable=False, comment="实际工价")
    quantity = db.Column(db.Integer, nullable=False, comment="生产数量")
    total_wage = db.Column(Numeric(10, 2), nullable=False, comment="总工资")
    actual_group_size = db.Column(db.Integer, nullable=False, default=1, comment="实际参与的班组人数")
    remark = db.Column(db.String(200), comment="备注信息")

    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False, comment="关联的工人ID")
    worker = db.relationship('Worker', back_populates='wage_logs')

    process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False, comment="关联的工序")
    process = db.relationship('Process', back_populates='wage_logs')

    spec_model_id = db.Column(db.Integer, db.ForeignKey('spec_models.id'), nullable=False, comment="关联的规格型号ID")
    spec_model = db.relationship('SpecModel', back_populates='wage_logs')

    # wage_price_id = db.Column(db.Integer, db.ForeignKey('wage_prices.id'), comment="关联的工价ID")
    # wage_price = db.relationship('WagePrice')    # wage_price = db.relationship('WagePrice')