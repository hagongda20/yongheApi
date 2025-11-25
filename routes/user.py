# routes/user.py
from flask import Blueprint, request, jsonify
from models import User
from db_config import db
from datetime import datetime, timedelta
import jwt
from utils.decorators import login_required

user_bp = Blueprint('auth', __name__)
SECRET_KEY = 'dao-hao-shi-gou'

# 注册
@user_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'ok': False, 'msg': '用户名和密码不能为空'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'ok': False, 'msg': '用户名已存在'}), 400

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'ok': True, 'msg': '用户注册成功', 'data': new_user.to_dict()}), 201

# 登录
@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'ok': False, 'msg': '用户名或密码错误'}), 400


    # 生成新的 token
    token_payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=12),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')

    # 保存最新 token（用于顶号）
    user.last_login_token = token
    user.last_login_time = datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True, 'token': token, 'data': user.to_dict()})

# 修改用户密码
@user_bp.route('/<int:user_id>/password', methods=['PUT'])
@login_required
def update_user_password(user_id, current_user):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'ok': False, 'msg': '用户不存在'}), 404

    if user.id != current_user.id:
        return jsonify({'ok': False, 'msg': '只能修改自己的密码'}), 403

    data = request.json
    new_password = data.get('password')

    if not new_password:
        return jsonify({'ok': False, 'msg': '新密码不能为空'}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({'ok': True, 'msg': '密码修改成功'}), 200


# 获取用户
@user_bp.route('/info', methods=['GET'])
@login_required
def get_current_user_info(current_user):
    return jsonify({'ok': True,'data': current_user.to_dict()}), 200
