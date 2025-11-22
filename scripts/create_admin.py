"""
创建管理员用户脚本
"""
import sys
import os

# 确保可以从项目根目录导入
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app
from models import User
from db_config import db

def create_admin(username='admin', password='admin123'):
    """创建管理员用户"""
    with app.app_context():
        # 检查用户是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            # 如果存在，更新为管理员
            if existing_user.role != 'admin':
                existing_user.role = 'admin'
                existing_user.set_password(password)
                db.session.commit()
                print(f"✅ 用户 '{username}' 已更新为管理员")
            else:
                print(f"⚠️  用户 '{username}' 已经是管理员")
            return
        
        # 创建新管理员
        admin = User(username=username, role='admin')
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"✅ 管理员 '{username}' 创建成功！")
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
        print(f"   角色: admin")

if __name__ == '__main__':
    if len(sys.argv) == 3:
        username = sys.argv[1]
        password = sys.argv[2]
        create_admin(username, password)
    elif len(sys.argv) == 2:
        username = sys.argv[1]
        create_admin(username)
    else:
        print("用法:")
        print("  python create_admin.py [用户名] [密码]")
        print("  python create_admin.py admin admin123")
        print("\n使用默认值创建管理员...")
        create_admin()

