from functools import wraps
from flask import g, jsonify

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not getattr(g, 'current_user', None):
            return jsonify({
                'code': 401,
                'msg': '未登录或登录已失效'
            }), 401

        return f(*args, **kwargs)

    return wrapper


# 角色权限验证装饰器
def roles_required(*required_roles):
    """
    使用示例:
        @roles_required('管理员', '会计')
    """
    def decorator(f):
        @wraps(f)
        @login_required  # 先确保用户已登录
        def wrapper(*args, **kwargs):
            user = g.current_user
            role_names = [role.name for role in getattr(user, 'roles', [])]
            # print(f"用户角色: {role_names}")  # 可以打印调试

            # 检查是否有权限
            if not any(r in role_names for r in required_roles):
                return jsonify({'code': 403, 'msg': '权限不足'}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator