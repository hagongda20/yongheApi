# routes/auth.py
from flask import Blueprint, request, jsonify, g
from models import User, UserRegister, Role, UserRole
from db_config import db
import jwt
from datetime import datetime, timedelta
from utils.decorators import login_required, roles_required

auth_bp = Blueprint('auth', __name__)
SECRET_KEY = 'dao-hao-shi-gou'


# -----------------------------
# 登录
# -----------------------------
@auth_bp.route('/', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401

    # 获取角色名
    role_names = [r.name for r in user.roles]

    # 打印调试信息
    print('===== 登录用户信息 =====')
    print('user_id:', user.id)
    print('username:', user.username)
    print('roles:', role_names)
    print('========================')

    # 生成 JWT token
    token_payload = {
        'user_id': user.id,
        'username': user.username,
        'roles': role_names,
        'exp': datetime.utcnow() + timedelta(hours=12),
        'iat': datetime.utcnow()
    }

    token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')

    # 更新用户最后登录 token 和时间
    user.last_login_token = token
    user.last_login_time = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'code': 200,
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'roles': role_names
        }
    })


# -----------------------------
# 用户注册
# -----------------------------
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'success': False, 'message': '用户名已存在'}), 400

    reg = UserRegister(
        username=data['username'],
        real_name=data.get('real_name'),
        phone=data.get('phone'),
        remark=data.get('remark')
    )
    reg.set_password(data['password'])

    db.session.add(reg)
    db.session.commit()

    return jsonify({'success': True, 'message': '注册成功，等待审核'})


# -----------------------------
# 待审核注册列表
# -----------------------------
@auth_bp.route('/register/list', methods=['GET'])
@roles_required('管理员')
def register_list():
    items = UserRegister.query.order_by(
        UserRegister.created_at.desc()
    ).all()

    data = [{
        'id': i.id,
        'username': i.username,
        'real_name': i.real_name,
        'phone': i.phone,
        'status': i.status,
        'remark': i.remark,
        'reject_reason': i.reject_reason,
        'created_at': i.created_at.strftime('%Y-%m-%d %H:%M')
    } for i in items]

    return jsonify({'success': True, 'data': data})


# -----------------------------
# 审核通过
# -----------------------------
@auth_bp.route('/register/approve/<int:reg_id>', methods=['POST'])
@roles_required('管理员')
def approve_register(reg_id):
    reg = UserRegister.query.get_or_404(reg_id)

    if reg.status != '待审核':
        return jsonify({'code': 400, 'msg': '状态不可变更'}), 400

    # 创建用户
    user = User(
        username=reg.username,
        password_hash=reg.password_hash,
        real_name=reg.real_name,
        phone=reg.phone,
        remark=reg.remark
    )
    db.session.add(user)
    db.session.flush()  # 获取 user.id

    # 默认角色：普通用户
    role = Role.query.filter_by(name='普通用户').first()
    if role:
        db.session.add(UserRole(user_id=user.id, role_id=role.id))

    # 更新注册状态
    reg.status = '已通过'
    reg.reviewed_at = datetime.utcnow()
    reg.reviewed_by = g.current_user.id

    db.session.commit()

    return jsonify({'code': 0, 'msg': '审批通过'})


# -----------------------------
# 审核拒绝
# -----------------------------
@auth_bp.route('/register/reject/<int:reg_id>', methods=['POST'])
@roles_required('管理员')
def reject_register(reg_id):
    reg = UserRegister.query.get_or_404(reg_id)
    data = request.json
    reason = data.get('reason')

    if not reason:
        return jsonify({'success': False, 'message': '请填写拒绝原因'}), 400

    if reg.status != '待审核':
        return jsonify({'success': False, 'message': '状态不可变更'}), 400

    reg.status = '已拒绝'
    reg.reject_reason = reason
    reg.reviewed_at = datetime.utcnow()
    reg.reviewed_by = g.current_user.id

    db.session.commit()

    return jsonify({'success': True, 'message': '已拒绝'})
