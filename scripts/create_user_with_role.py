import sys
import os

# 确保可以从项目根目录导入
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app
from models import User, Role, UserRole
from db_config import db


def create_user_with_role(username: str, password: str, role_name: str):
    with app.app_context():
        # 1️⃣ 检查用户是否存在
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"❌ 用户 '{username}' 已存在")
            return

        # 2️⃣ 检查角色是否存在
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            print(f"❌ 角色 '{role_name}' 不存在，请先创建角色")
            return

        # 3️⃣ 创建用户
        user = User(username=username)
        user.set_password(password)

        db.session.add(user)
        db.session.flush()  # 获取 user.id

        # 4️⃣ 绑定角色
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db.session.add(user_role)

        db.session.commit()

        print(f"✅ 用户 '{username}' 创建成功，角色：{role_name}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("用法: python scripts/create_user_with_role.py 用户名 密码 角色名")
        print("示例: python scripts/create_user_with_role.py admin admin123 管理员")
    else:
        username = sys.argv[1]
        password = sys.argv[2]
        role_name = sys.argv[3]

        create_user_with_role(username, password, role_name)
