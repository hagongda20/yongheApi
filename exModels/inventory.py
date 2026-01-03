# exModels/inventory.py
"""
库存与规格系统最终模型文件（修正版）

设计总原则：
1. 规格 = 可扩展的结构化配置(不直接参与库存)
2. 产品 = 一组规格的“确定组合结果”
3. 产品名称 = 规格生成的默认名 + 可人工调整
4. 库存 = 某厂区(company)下某产品的库存状态（账，不删除）
5. 库存流水 = 所有库存变化的唯一审计来源（只增不改）
"""

from datetime import datetime
from db_config import db


# ==================================================
# 基类：统一时间戳
# ==================================================
class TimestampMixin:
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='创建时间'
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment='更新时间'
    )


# ==================================================
# 一、规格体系（配置层）
# ==================================================

class SpecCategory(db.Model):
    """
    规格分类定义（软停用）
    """
    __tablename__ = 'spec_categories'

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        comment='规格编码，如 length / thickness'
    )
    name = db.Column(
        db.String(50),
        nullable=False,
        comment='规格名称'
    )
    sort_order = db.Column(
        db.Integer,
        default=0,
        comment='排序'
    )
    is_active = db.Column(
        db.Boolean,
        default=True,
        comment='是否启用'
    )


class SpecOption(db.Model):
    """
    规格可选值（软停用）
    """
    __tablename__ = 'spec_options'

    id = db.Column(db.Integer, primary_key=True)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey('spec_categories.id'),
        nullable=False,
        comment='规格分类ID'
    )

    value = db.Column(
        db.String(100),
        nullable=False,
        comment='规格值'
    )

    sort_order = db.Column(
        db.Integer,
        default=0,
        comment='排序'
    )
    is_active = db.Column(
        db.Boolean,
        default=True,
        comment='是否启用'
    )


# ==================================================
# 二、产品（规格组合后的确定成品）
# ==================================================

class Product(db.Model, TimestampMixin):
    """
    产品 = 一组规格组合后的结果
    spec_json 是系统判定“是不是同一个产品”的唯一依据
    """
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(200),
        nullable=False,
        comment='产品名称（规格生成后可人工调整）'
    )

    spec_json = db.Column(
        db.JSON,
        nullable=False,
        comment='规格组合JSON（系统唯一识别依据）'
    )

    code = db.Column(
        db.String(100),
        unique=True,
        nullable=True,
        comment='产品编码（对外 / ERP）'
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        comment='是否在用（停用不影响历史数据）'
    )

    remark = db.Column(
        db.String(255),
        nullable=True,
        comment='备注'
    )

    inventories = db.relationship(
        'Inventory',
        backref='product',
        lazy=True
    )


# ==================================================
# 三、库存（厂区 / 公司维度）
# ==================================================

class Inventory(db.Model, TimestampMixin):
    """
    库存 = 某厂区(company)下某产品的库存账
    库存记录不删除，只能冻结或清零
    """
    __tablename__ = 'inventories'

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id'),
        nullable=False,
        comment='产品ID'
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id'),
        nullable=False,
        comment='厂区 / 公司ID'
    )

    display_name = db.Column(
        db.String(200),
        nullable=False,
        comment='厂区内部库存叫法（别名）'
    )

    quantity = db.Column(
        db.Integer,
        default=0,
        comment='当前库存数量'
    )

    warning_min_quantity = db.Column(
        db.Integer,
        default=0,
        comment='库存预警下限'
    )

    warning_max_quantity = db.Column(
        db.Integer,
        nullable=True,
        comment='库存预警上限'
    )

    cost_price = db.Column(
        db.Numeric(10, 2),
        nullable=True,
        comment='参考成本价'
    )

    is_frozen = db.Column(
        db.Boolean,
        default=False,
        comment='是否冻结（冻结后禁止出入库）'
    )


# ==================================================
# 四、库存流水（唯一审计来源）
# ==================================================

class InventoryLog(db.Model, TimestampMixin):
    """
    所有库存变化必须落到此表
    只能新增，禁止删除 / 修改
    """
    __tablename__ = 'inventory_logs'

    id = db.Column(db.Integer, primary_key=True)

    inventory_id = db.Column(
        db.Integer,
        db.ForeignKey('inventories.id'),
        nullable=False,
        comment='库存ID'
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id'),
        nullable=False,
        comment='操作所属厂区 / 公司'
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False,
        comment='操作用户ID'
    )

    action = db.Column(
        db.String(20),
        nullable=False,
        comment='操作类型：in / out / adjust'
    )

    change_quantity = db.Column(
        db.Integer,
        nullable=False,
        comment='变动数量（正负）'
    )

    before_quantity = db.Column(
        db.Integer,
        nullable=False,
        comment='变动前库存'
    )

    after_quantity = db.Column(
        db.Integer,
        nullable=False,
        comment='变动后库存'
    )

    remark = db.Column(
        db.String(255),
        nullable=True,
        comment='备注'
    )


# ==================================================
# 五、库存盘点单
# ==================================================

class InventoryCheck(db.Model, TimestampMixin):
    """
    一次盘点任务（按厂区）
    """
    __tablename__ = 'inventory_checks'

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id'),
        nullable=False,
        comment='盘点厂区 / 公司ID'
    )

    status = db.Column(
        db.String(20),
        default='pending',
        comment='状态：pending / confirmed / canceled'
    )

    remark = db.Column(
        db.String(255),
        nullable=True,
        comment='备注'
    )

    items = db.relationship(
        'InventoryCheckItem',
        backref='check',
        lazy=True
    )


class InventoryCheckItem(db.Model, TimestampMixin):
    """
    盘点明细
    """
    __tablename__ = 'inventory_check_items'

    id = db.Column(db.Integer, primary_key=True)

    check_id = db.Column(
        db.Integer,
        db.ForeignKey('inventory_checks.id'),
        nullable=False,
        comment='盘点单ID'
    )

    inventory_id = db.Column(
        db.Integer,
        db.ForeignKey('inventories.id'),
        nullable=False,
        comment='库存ID'
    )

    system_quantity = db.Column(
        db.Integer,
        nullable=False,
        comment='系统库存数量'
    )

    actual_quantity = db.Column(
        db.Integer,
        nullable=False,
        comment='实际盘点数量'
    )

    difference = db.Column(
        db.Integer,
        nullable=False,
        comment='盘点差异（实际 - 系统）'
    )
