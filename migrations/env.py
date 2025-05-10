import logging
from logging.config import fileConfig
from flask import current_app
from alembic import context
from models import db  # 导入 db 对象，确保你的 models 已加载

# Alembic 的配置对象，提供对 .ini 文件的访问
config = context.config

# 设置日志配置
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# 使用 db.metadata 作为 Alembic 的 target_metadata
target_metadata = db.metadata

def get_engine():
    """获取数据库连接引擎"""
    try:
        # Flask-SQLAlchemy < 3
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # Flask-SQLAlchemy >= 3
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    """返回数据库连接的 URL"""
    try:
        return get_engine().url.render_as_string(hide_password=False).replace('%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')


# 设置 SQLAlchemy URL 配置
config.set_main_option('sqlalchemy.url', get_engine_url())

# 获取数据库的元数据
def get_metadata():
    """获取数据库元数据"""
    if hasattr(current_app.extensions['migrate'].db, 'metadatas'):
        return current_app.extensions['migrate'].db.metadatas[None]
    return current_app.extensions['migrate'].db.metadata


def run_migrations_offline():
    """以离线模式运行迁移"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """以在线模式运行迁移"""
    def process_revision_directives(context, revision, directives):
        """用于防止在没有 schema 变化时生成迁移"""
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    # 配置进程修订指令
    conf_args = current_app.extensions['migrate'].configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()


# 根据是否是离线模式来运行迁移
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
