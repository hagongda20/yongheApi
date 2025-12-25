from flask import Flask, g, request, current_app
from flask_cors import CORS
from flask_migrate import Migrate
from db_config import db, init_db_config
from routes.auth import auth_bp
from routes.worker import worker_bp
from routes.process import process_bp
from routes.spec_model import spec_model_bp
from routes.wagelog import wagelog_bp
from routes.company_ledger.company import company_bp
from routes.company_ledger.customer import customer_bp
from routes.company_ledger.customer_account import customer_account_bp
from routes.company_ledger.company_account import company_account_bp
from routes.company_ledger.customer_balance import customer_balance_bp
from routes.company_ledger.transaction_routes import transaction_bp

from models import User
import jwt

app = Flask(__name__)
CORS(app)

# 初始化数据库配置
init_db_config(app)

# 数据迁移工具初始化
migrate = Migrate(app, db)

# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/api/users')
app.register_blueprint(worker_bp, url_prefix="/api/workers")
app.register_blueprint(process_bp, url_prefix='/api/processes')
app.register_blueprint(spec_model_bp, url_prefix='/api/specmodels')
app.register_blueprint(wagelog_bp, url_prefix='/api/wage_logs')
app.register_blueprint(company_bp, url_prefix='/api/company')
app.register_blueprint(customer_bp, url_prefix='/api/customer')
app.register_blueprint(customer_account_bp, url_prefix='/api/customer_account')
app.register_blueprint(company_account_bp, url_prefix='/api/company_account')
app.register_blueprint(customer_balance_bp, url_prefix='/api/customer_balance')
app.register_blueprint(transaction_bp, url_prefix='/api/transaction')

# -------------------------------
# 全局 before_request: 加载当前用户
# -------------------------------
@app.before_request
def load_current_user():
    g.current_user = None

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return

    # 兼容 Bearer token
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
    else:
        token = auth_header

    try:
        data = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )

        user = User.query.get(data.get('user_id'))
        if not user:
            return

        # 顶号校验
        if user.last_login_token != token:
            return

        g.current_user = user
        # print('当前用户:', user.username)

    except jwt.ExpiredSignatureError:
        pass
    except jwt.InvalidTokenError:
        pass

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=6000)
