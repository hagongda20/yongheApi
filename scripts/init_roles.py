# scripts/init_roles.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app
from models import Role
from db_config import db

def init_roles():
    with app.app_context():
        roles = [
            ('管理员', '系统管理员'),
            ('普通用户', '普通系统用户'),
        ]

        for name, desc in roles:
            if not Role.query.filter_by(name=name).first():
                db.session.add(Role(name=name, description=desc))

        db.session.commit()
        print("✅ 角色初始化完成")

if __name__ == "__main__":
    init_roles()
