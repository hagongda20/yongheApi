# utils/decorators.py
from flask import request, jsonify
import jwt
from models import User

SECRET_KEY = 'dao-hao-shi-gou'

def login_required(f):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        print("token:", token)
        if not token:
            return jsonify({'code': 401, 'msg': '未登录'}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user = User.query.get(data['user_id'])
            if not user or user.last_login_token != token:
                return jsonify({'code': 401, 'msg': '登录已失效或被顶号'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'code': 401, 'msg': '登录已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'code': 401, 'msg': '无效的登录信息'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper
