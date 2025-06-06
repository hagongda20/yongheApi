"""删除工价表,工价合并到规格表,并调整其他表

Revision ID: bc4aa4447575
Revises: acabcf3f715d
Create Date: 2025-05-07 20:02:07.088012

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'bc4aa4447575'
down_revision = 'acabcf3f715d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('wage_prices')
    with op.batch_alter_table('spec_models', schema=None) as batch_op:
        batch_op.add_column(sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False))

    with op.batch_alter_table('wage_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_special', sa.Boolean(), nullable=True))

    with op.batch_alter_table('workers', schema=None) as batch_op:
        batch_op.drop_index('id_card')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('workers', schema=None) as batch_op:
        batch_op.create_index('id_card', ['id_card'], unique=True)

    with op.batch_alter_table('wage_logs', schema=None) as batch_op:
        batch_op.drop_column('is_special')

    with op.batch_alter_table('spec_models', schema=None) as batch_op:
        batch_op.drop_column('price')

    op.create_table('wage_prices',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('price', mysql.DECIMAL(precision=10, scale=2), nullable=False),
    sa.Column('is_special', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.Column('spec_model_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('created_at', mysql.DATETIME(), nullable=True),
    sa.Column('updated_at', mysql.DATETIME(), nullable=True),
    sa.Column('process_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['process_id'], ['processes.id'], name='wage_prices_ibfk_2'),
    sa.ForeignKeyConstraint(['spec_model_id'], ['spec_models.id'], name='wage_prices_ibfk_1'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_unicode_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    # ### end Alembic commands ###
