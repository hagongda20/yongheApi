import sys
import os
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from app import app
from db_config import db


def safe_database_reset():
    try:
        with app.app_context():
            print("🛡️  开始安全重置数据库...")

            # 禁用外键约束
            print("🔓 禁用外键约束...")
            db.session.execute(text('SET FOREIGN_KEY_CHECKS = 0;'))
            db.session.commit()

            # 删除所有表
            print("🗑️  删除所有表...")
            db.drop_all()
            db.session.commit()

            # 重新启用外键约束
            print("🔒 恢复外键约束...")
            db.session.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))
            db.session.commit()

            # 重新创建表
            print("🔨 重新创建表结构...")
            db.create_all()
            db.session.commit()

            print("✅ 数据库安全重置完成！")

    except SQLAlchemyError as e:
        print(f"❌ 数据库错误: {e}")
        db.session.rollback()
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        db.session.rollback()
    finally:
        # 确保外键约束总是被恢复
        try:
            with app.app_context():
                db.session.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))
                db.session.commit()
        except:
            pass


if __name__ == '__main__':
    safe_database_reset()