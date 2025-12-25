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

    is_active = db.Column(db.Boolean, default=True)  # 激活状态可用
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # 创建时间

    # 新增注册表对应字段
    real_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    remark = db.Column(db.String(255))

    # ⭐ 关键：角色关联
    roles = db.relationship(
        'Role',
        secondary='user_roles',
        backref='users'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# 注册申请表
class UserRegister(db.Model):
    __tablename__ = 'user_registers'

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), nullable=False)      
    password_hash = db.Column(db.String(128), nullable=False)

    real_name = db.Column(db.String(50))  # 真实姓名，用于锁定记录者
    phone = db.Column(db.String(20))     # 
    remark = db.Column(db.String(255))  # 备注

    # 状态：待审核 / 已通过 / 已拒绝
    status = db.Column(db.String(20), default='待审核')

    reject_reason = db.Column(db.String(255))    # 拒绝原因

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)   # 审核时间

    reviewed_by = db.Column(db.Integer)  # 管理员 user.id

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password, method='pbkdf2:sha256'
        )


#角色表
class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))


#用户-角色关联表
class UserRole(db.Model):
    __tablename__ = 'user_roles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)


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



# 12。04 #
# -------------------------------
# 公司表：三个公司独立核算
# -------------------------------
class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)  # 公司ID，自增主键
    name = db.Column(db.String(100), unique=True, nullable=False)  # 公司名称，如：A公司、B公司、C公司，唯一且必填
    description = db.Column(db.String(200)) # 公司描述或业务范围，可选
    remark = db.Column(db.String(200)) # 备注，用于记录其他额外信息或说明

    # 关系
    bank_accounts = db.relationship('CompanyAccount', back_populates='company')
    customer_balances = db.relationship('CustomerBalance', back_populates='company')
    transactions = db.relationship('Transaction', back_populates='company')

# -------------------------------
# 客户表：记录公司所有客户信息
# -------------------------------
class Customer(db.Model, TimestampMixin):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True) # 客户ID，自增主键
    name = db.Column(db.String(100), nullable=False) # 客户名称，必填
    type = db.Column(
        db.Enum('供应商','客户','个人','其他', name='customer_type'),
        nullable=False
    )
    # 客户类型：supplier=供应商客户, sales=销售客户, other=其他
    phone = db.Column(db.String(50)) # 客户联系电话，可选
    company = db.Column(db.String(100)) # 客户所属单位/公司名称（非本公司），可选
    is_deleted = db.Column(db.Boolean, default=False, nullable=False) # 软删除标识：True=已删除, False=正常
    deleted_at = db.Column(db.DateTime) # 删除时间，可选
    remark = db.Column(db.String(200)) # 客户备注，可用于记录合同号、特殊协议、业务说明等

    # 关系
    accounts = db.relationship('CustomerAccount', back_populates='customer')
    transactions = db.relationship('Transaction', back_populates='customer')
    balances = db.relationship('CustomerBalance', back_populates='customer')
    adjustments = db.relationship('AdjustmentLog', back_populates='customer')

# -------------------------------
# 客户支付账户表
# -------------------------------
class CustomerAccount(db.Model, TimestampMixin):
    __tablename__ = 'customer_accounts'

    id = db.Column(db.Integer, primary_key=True) # 客户支付账户ID，自增主键
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False) # 所属客户ID，外键
    account_type = db.Column(
        db.Enum('银行','微信','支付宝','现金','其他', name='account_type'),
        nullable=False
    )
    # 账户类型：bank=银行卡, wechat=微信, alipay=支付宝, other=其他
    account_no = db.Column(db.String(50)) # 账户号，例如银行卡号/支付宝账号/微信号
    bank_name = db.Column(db.String(100)) # 银行名称，仅银行卡类型填写
    is_deleted = db.Column(db.Boolean, default=False, nullable=False) # 软删除标识
    deleted_at = db.Column(db.DateTime) # 删除时间，可选
    remark = db.Column(db.String(200)) # 账户备注，可用于记录用途、关联合同等

    # 关系
    customer = db.relationship('Customer', back_populates='accounts')
    transactions = db.relationship('Transaction', back_populates='customer_account')

    # -------------------------------
    # 序列化方法
    # -------------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "customer_name": self.customer.name if self.customer else None,
            "account_type": self.account_type,
            "account_no": self.account_no,
            "bank_name": self.bank_name,
            "remark": self.remark,
            "is_deleted": self.is_deleted
        }


# -------------------------------
# 公司账户表
# -------------------------------
class CompanyAccount(db.Model, TimestampMixin):
    __tablename__ = 'company_accounts'

    id = db.Column(db.Integer, primary_key=True) # 公司账户ID，自增主键
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False) # 所属公司ID，外键
    account_name = db.Column(db.String(100), nullable=False) # 账户用途或名称，例如“收款账户A”
    account_type = db.Column(
        db.Enum('银行','微信','支付宝','现金','其他', name='company_account_type'),
        nullable=False
    )
    # 账户类型
    account_no = db.Column(db.String(50), nullable=False) # 账户号
    bank_name = db.Column(db.String(100)) # 银行名称，仅银行账户填写
    currency = db.Column(db.String(10), default='CNY') # 币种，默认人民币
    balance = db.Column(Numeric(12,2), default=0) # 当前余额，正数表示账户内实际金额

    status = db.Column(
        db.Enum('正常','停用', name='company_account_status'),
        default='正常'
    )
    # 账户状态：active=正常, inactive=停用

    remark = db.Column(db.String(200)) # 备注，可记录用途、负责人、特殊说明等

    # 关系
    company = db.relationship('Company', back_populates='bank_accounts')
    transactions = db.relationship('Transaction', back_populates='company_account')


# -------------------------------
# 转账流水表
# -------------------------------
class Transaction(db.Model, TimestampMixin):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True) # 流水ID，自增主键
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False) # 所属公司ID
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False) # 客户ID
    customer_account_id = db.Column(db.Integer, db.ForeignKey('customer_accounts.id')) # 客户支付账户ID，可选
    company_account_id = db.Column(db.Integer, db.ForeignKey('company_accounts.id'), nullable=False) # 公司账户ID
    amount = db.Column(Numeric(12,2), nullable=False) # 流水金额，**正数表示金额实际流动**    # 查询时通过 direction 判断收入/支出

    direction = db.Column(
        db.Enum('收入','支出', name='transaction_direction'),
        nullable=False
    )   # 流水方向：income=收入(客户付款给公司), expense=支出(公司付款给客户)

    method = db.Column(
        db.Enum('银行','微信','支付宝','现金','其他',  name='transaction_method'),
        nullable=False
    )  # 支付方式

    reference_no = db.Column(db.String(100)) # 银行流水号或第三方交易号

    status = db.Column(
        db.Enum('待处理','已到账','失败', name='transaction_status'),
        default='已到账'
    )
    # 流水状态：pending=待处理, received=已到账, failed=失败

    remark = db.Column(db.String(200))  # 备注，可记录业务说明、合同号、发票号等

    # 关系
    company = db.relationship('Company', back_populates='transactions')
    customer = db.relationship('Customer', back_populates='transactions')
    customer_account = db.relationship('CustomerAccount', back_populates='transactions')
    company_account = db.relationship('CompanyAccount', back_populates='transactions')
    adjustments = db.relationship('AdjustmentLog', back_populates='transaction')


# -------------------------------
# 客户余额表
# -------------------------------
class CustomerBalance(db.Model, TimestampMixin):
    __tablename__ = 'customer_balances'

    id = db.Column(db.Integer, primary_key=True) # 主键ID
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False) # 客户ID
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False) # 公司ID

    __table_args__ = (
        db.UniqueConstraint('customer_id', 'company_id', name='uq_customer_company'),
    )
    # 每个客户在每个公司下唯一

    balance = db.Column(Numeric(12, 2, asdecimal=True), default=0, nullable=False)
    adjustment_total = db.Column(Numeric(12, 2, asdecimal=True), default=0, nullable=False)

    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    # 更新时间，每次余额变动自动更新

    remark = db.Column(db.String(200)) # 备注，可记录余额计算规则或业务说明

    # 关系
    customer = db.relationship('Customer', back_populates='balances')
    company = db.relationship('Company', back_populates='customer_balances')
    adjustments = db.relationship('AdjustmentLog', back_populates='customer_balance')


# -------------------------------
# 调账流水表
# -------------------------------
class AdjustmentLog(db.Model, TimestampMixin):
    __tablename__ = 'adjustment_logs'

    id = db.Column(db.Integer, primary_key=True) # 调账ID
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False) # 客户ID
    customer_balance_id = db.Column(db.Integer, db.ForeignKey('customer_balances.id'), nullable=False) # 客户余额ID
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id')) # 可选，关联原流水
    amount = db.Column(Numeric(12,2), nullable=False)
    # 调整金额，**始终正数**
    # type 字段决定是增加余额还是减少余额
    type = db.Column(
        db.Enum('抹零','勾账','手动调整', name='adjustment_type'),
        nullable=False
    )
    # 调整类型：rounding=抹零, write_off=勾账, manual=手动调整

    remark = db.Column(db.String(200))
    # 备注，可记录调整原因、责任人、审批信息等

    # 关系
    customer = db.relationship('Customer', back_populates='adjustments')
    customer_balance = db.relationship('CustomerBalance', back_populates='adjustments')
    transaction = db.relationship('Transaction', back_populates='adjustments')
