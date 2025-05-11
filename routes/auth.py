# routes/auth.py
from flask import Blueprint, request, jsonify
from models import User 
from db_config import db
import jwt, datetime

auth_bp = Blueprint('auth', __name__)
SECRET_KEY = 'dao-hao-shi-gou'

# 登录
@auth_bp.route('/', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    print("username:",username,"password:",password,"user:",user)
    if not user or not user.check_password(password):
        return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401

    # 生成新的 token
    token_payload = {
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12),
        'iat': datetime.datetime.utcnow()
    }
    token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')

    # 保存最新 token（用于顶号）
    user.last_login_token = token
    user.last_login_time = datetime.datetime.utcnow()
    db.session.commit()
    print("********登录成功********")
    return jsonify({'code': 200, 'token': token, 'username': user.username})
