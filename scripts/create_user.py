import sys
import os

# 确保可以从项目根目录导入 app.py 和 models.py
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app              # 从 app.py 导入 app 实例
from models import  User      # 导入数据库和 User 模型
from db_config import db

def create_user(username: str, password: str):
    with app.app_context():
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"❌ 用户 '{username}' 已存在")
            return

        new_user = User(username=username)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()
        print(f"✅ 用户 '{username}' 创建成功")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("用法: python scripts/create_user.py 用户名 密码")
    else:
        username = sys.argv[1]
        password = sys.argv[2]
        create_user(username, password)