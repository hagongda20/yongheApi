# utils/decorators.py
from flask import request, jsonify
import jwt
from functools import wraps
from models import User

SECRET_KEY = 'dao-hao-shi-gou'

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'ok': False, 'msg': '未登录'}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user = User.query.get(data['user_id'])
            if not user or user.last_login_token != token:
                return jsonify({'ok': False, 'msg': '登录已失效或被顶号'}), 401
            kwargs['current_user'] = user
        except jwt.ExpiredSignatureError:
            return jsonify({'ok': False, 'msg': '登录已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'ok': False, 'msg': '无效的登录信息'}), 401
        except Exception as e:
            return jsonify({'ok': False, 'msg': '服务器错误', 'error': str(e)}), 500
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if not current_user or not current_user.is_admin():
            return jsonify({'ok': False, 'msg': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return wrapper

def role_required(*roles):
    """指定角色权限装饰器（需要先登录）"""
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or current_user.role not in roles:
                return jsonify({
                    'code': 403, 
                    'msg': f'需要以下角色之一: {", ".join(roles)}'
                }), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
