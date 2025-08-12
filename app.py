from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from db_config import db, init_db_config
from routes.auth import auth_bp
from routes.worker import worker_bp
from routes.process import process_bp
from routes.spec_model import spec_model_bp
from routes.wagelog import wagelog_bp

import models

app = Flask(__name__)
CORS(app)

# 初始化数据库配置
init_db_config(app)


# 数据迁移工具初始化
migrate = Migrate(app, db)

# 注册蓝图
# app.register_blueprint(api_bp, url_prefix="/api")
app.register_blueprint(auth_bp, url_prefix='/api/users') # 注册工资记录蓝图
app.register_blueprint(worker_bp, url_prefix="/api/workers")  # 注册工人蓝图
app.register_blueprint(process_bp, url_prefix='/api/processes') # 注册工序蓝图
app.register_blueprint(spec_model_bp, url_prefix='/api/specmodels') # 注册规格蓝图
# app.register_blueprint(wage_price_bp, url_prefix='/api/wageprice') # 注册工价蓝图
app.register_blueprint(wagelog_bp, url_prefix='/api/wage_logs') # 注册工资记录蓝图


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=6000)
