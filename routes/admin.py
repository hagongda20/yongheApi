# routes/admin.py
from flask import Blueprint, request, jsonify
from models import User
from db_config import db
from utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__)

# 获取用户列表
@admin_bp.route('/', methods=['GET'])
@admin_required
def get_users():
    try:
        users = User.query.all()
        users_list = [user.to_dict() for user in users]
        return jsonify({'ok': True, 'data': users_list }), 200
    except Exception as e:
        return jsonify({'ok': False, 'msg': '获取用户列表失败', 'error': str(e)}), 500

# 获取单个用户信息
@admin_bp.route('/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'ok': False, 'msg': '用户不存在'}), 404
    return jsonify({'ok': True, 'user': user.to_dict()}), 200


# 修改用户角色
@admin_bp.route('/<int:user_id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id, current_user):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'ok': False, 'msg': '用户不存在'}), 404

    if user.id == current_user.id:
        return jsonify({'ok': False, 'msg': '不能修改自己的角色'}), 400

    data = request.json
    new_role = data.get('role')

    if new_role not in ['admin', 'user']:
        return jsonify({'ok': False, 'msg': '无效的角色，只能是 admin 或 user'}), 400

    user.role = new_role
    db.session.commit()

    return jsonify({'ok': True,'msg': '角色修改成功','data': user.to_dict()}), 200


# 删除用户
@admin_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id, current_user):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'ok': False, 'msg': '用户不存在'}), 404

    if user.id == current_user.id:
        return jsonify({'ok': False, 'msg': '不能删除自己'}), 400

    db.session.delete(user)
    db.session.commit()

    return jsonify({'ok': False, 'msg': '用户删除成功'}), 200

