"""
清理遗留 ORM / 外键逻辑，不新建表，不新建约束
仅用于保证迁移链与当前模型一致

Revision ID: a1b2c3d4e5f6
Revises: 6794e3e31ba3
Create Date: 2025-12-27
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '6794e3e31ba3'
branch_labels = None
depends_on = None


def upgrade():
    """
    ⚠️ 只做「已有表的修改」
    ⚠️ 不 create_table
    ⚠️ 不 create_foreign_key
    """

    # 如果 users 表中 company_id 字段存在但你不想用外键
    # 这里什么都不用写（Alembic 不强制必须有内容）
    pass


def downgrade():
    """
    不支持回滚（结构清理型迁移，允许空）
    """
    pass
