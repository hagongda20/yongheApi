from flask import Blueprint, request, jsonify, g
from db_config import db
from utils.decorators import login_required, roles_required
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from models import User
from exModels.inventory import InventoryLog, Inventory, Product

from exModels.inventory import (
    SpecCategory,
    SpecOption,
    Product,
    Inventory,
    InventoryLog,
    InventoryCheck,
    InventoryCheckItem
)

inventory_bp = Blueprint('inventory', __name__)

# ==================================================
# 一、规格管理
# ==================================================

# 获取全部规格（仅启用）
@inventory_bp.route('/spec/list', methods=['GET'])
def get_specs():
    categories = SpecCategory.query.filter_by(
        is_active=True
    ).order_by(SpecCategory.sort_order).all()

    result = []
    for c in categories:
        options = SpecOption.query.filter_by(
            category_id=c.id,
            is_active=True
        ).order_by(SpecOption.sort_order).all()

        result.append({
            'id': c.id,
            'code': c.code,
            'name': c.name,
            'options': [
                {'id': o.id, 'value': o.value}
                for o in options
            ]
        })

    return jsonify(success=True, data=result)


# 新增规格分类
@inventory_bp.route('/spec/category/add', methods=['POST'])
def add_spec_category():
    data = request.json

    if SpecCategory.query.filter_by(code=data['code']).first():
        return jsonify(success=False, message='规格编码已存在')

    category = SpecCategory(
        code=data['code'],
        name=data['name'],
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(category)
    db.session.commit()

    return jsonify(success=True, data={'id': category.id})


# 更新规格分类
@inventory_bp.route('/spec/category/update', methods=['POST'])
def update_spec_category():
    data = request.json
    category = SpecCategory.query.get_or_404(data['id'])

    category.name = data.get('name', category.name)
    category.sort_order = data.get('sort_order', category.sort_order)

    db.session.commit()
    return jsonify(success=True)


# 停用规格分类（软删除）
@inventory_bp.route('/spec/category/disable', methods=['POST'])
def disable_spec_category():
    category = SpecCategory.query.get_or_404(request.json['id'])

    # 已被产品使用，禁止停用
    used = Product.query.filter(
        Product.spec_json[category.code].isnot(None)
    ).first()

    if used:
        return jsonify(success=False, message='该规格分类已被产品使用，禁止停用')

    category.is_active = False
    db.session.commit()
    return jsonify(success=True)


# 新增规格选项
@inventory_bp.route('/spec/option/add', methods=['POST'])
def add_spec_option():
    data = request.json

    option = SpecOption(
        category_id=data['category_id'],
        value=data['value'],
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(option)
    db.session.commit()

    return jsonify(success=True, data={'id': option.id})


# 更新规格选项
@inventory_bp.route('/spec/option/update', methods=['POST'])
def update_spec_option():
    data = request.json
    option = SpecOption.query.get_or_404(data['id'])

    option.value = data.get('value', option.value)
    option.sort_order = data.get('sort_order', option.sort_order)

    db.session.commit()
    return jsonify(success=True)


# 停用规格选项（软删除）
@inventory_bp.route('/spec/option/disable', methods=['POST'])
def disable_spec_option():
    option = SpecOption.query.get_or_404(request.json['id'])
    category = SpecCategory.query.get(option.category_id)

    used = Product.query.filter(
        Product.spec_json[category.code] == option.value
    ).first()

    if used:
        return jsonify(success=False, message='该规格值已被产品使用，禁止停用')

    option.is_active = False
    db.session.commit()
    return jsonify(success=True)


# ==================================================
# 二、产品管理
# ==================================================

@inventory_bp.route('/product/add', methods=['POST'])
def create_product():
    data = request.json
    spec_json = data.get('spec_json')

    if not spec_json or not isinstance(spec_json, dict):
        return jsonify(success=False, message='规格数据不合法')

    exists = Product.query.filter(
        Product.spec_json == spec_json
    ).first()

    if exists:
        return jsonify(
            success=False,
            message='该规格组合的产品已存在',
            data={'product_id': exists.id}
        )

    default_name = ' '.join(spec_json.values())

    product = Product(
        name=data.get('name') or default_name,
        spec_json=spec_json,
        code=data.get('code'),
        remark=data.get('remark')
    )
    db.session.add(product)
    db.session.commit()

    return jsonify(success=True, data={'id': product.id})


@inventory_bp.route('/product/list', methods=['GET'])
def list_products():
    products = Product.query.order_by(Product.created_at.desc()).all()

    return jsonify(success=True, data=[
        {
            'id': p.id,
            'name': p.name,
            'spec_json': p.spec_json,
            'code': p.code,
            'remark': p.remark
        }
        for p in products
    ])


# ==================================================
# 三、库存管理
# ==================================================
# 库存新增
@inventory_bp.route('/inventory/add', methods=['POST'])
def create_inventory():
    data = request.json

    inventory = Inventory(
        product_id=data['product_id'],
        company_id=g.current_user.company_id,
        display_name=data['display_name'],
        quantity=data.get('quantity', 0),
        warning_min_quantity=data.get('warning_min_quantity', 0),
        warning_max_quantity=data.get('warning_max_quantity'),
        cost_price=data.get('cost_price')
    )
    db.session.add(inventory)
    db.session.commit()

    return jsonify(success=True, data={'id': inventory.id})

# 库存台账列表
@inventory_bp.route('/inventory/list', methods=['GET'])
@login_required
def list_inventories():
    company_id = g.current_user.company_id

    inventories = Inventory.query.filter_by(
        company_id=company_id
    ).all()

    return jsonify(success=True, data=[
        {
            'id': i.id,
            'product_id': i.product_id,

            # ✅ 产品层信息（前端要的）
            'product_name': i.product.name if i.product else '',
            'spec_json': i.product.spec_json if i.product else {},

            # ✅ 库存自身信息
            'display_name': i.display_name,
            'quantity': i.quantity,
            'warning_min_quantity': i.warning_min_quantity,
            'warning_max_quantity': i.warning_max_quantity,
            'is_frozen': i.is_frozen,
        }
        for i in inventories
    ])

# 更新库存台账信息，只更新一些辅助字段，如别名（显示名称）、预警上下限等
@inventory_bp.route('/inventory/update', methods=['POST'])
@login_required
def update_inventory():
    data = request.json or {}
    inventory_id = data.get('id')

    if not inventory_id:
        return jsonify({'success': False, 'msg': '缺少库存ID'}), 400

    inventory = Inventory.query.filter_by(
        id=inventory_id,
        company_id=g.current_user.company_id
    ).first()

    if not inventory:
        return jsonify({'success': False, 'msg': '库存不存在或无权限'}), 404

    # ====== 只允许修改的字段 ======
    if 'display_name' in data:
        inventory.display_name = data['display_name']

    if 'warning_min_quantity' in data:
        inventory.warning_min_quantity = data['warning_min_quantity'] or 0

    if 'warning_max_quantity' in data:
        inventory.warning_max_quantity = data['warning_max_quantity']

    if 'cost_price' in data:
        inventory.cost_price = data['cost_price']

    if 'is_frozen' in data:
        inventory.is_frozen = bool(data['is_frozen'])

    db.session.commit()

    return jsonify({
        'success': True,
        'msg': '库存信息更新成功'
    })



# 库存变更（唯一入口）
@inventory_bp.route('/inventory/change', methods=['POST'])
@login_required
def change_inventory():
    """
    库存变更接口：
    - in: 入库，必须 >0
    - out: 出库，必须 >0
    - adjust: 调整，可正可负
    """
    data = request.json or {}

    inventory_id = data.get('inventory_id')
    action = data.get('action')
    quantity = data.get('quantity')  # 前端直接传正负数
    remark = data.get('remark', '')

    if action not in ('in', 'out', 'adjust'):
        return jsonify(success=False, message='非法操作类型'), 400

    if quantity is None:
        return jsonify(success=False, message='数量不能为空'), 400

    try:
        quantity = int(quantity)
    except ValueError:
        return jsonify(success=False, message='数量必须为整数'), 400

    # 入库出库必须 >0
    if action in ('in', 'out') and quantity <= 0:
        return jsonify(success=False, message=f'{action}数量必须大于0'), 400

    inventory = Inventory.query.filter_by(
        id=inventory_id,
        company_id=g.current_user.company_id
    ).first()

    if not inventory:
        return jsonify(success=False, message='库存不存在或无权限'), 404

    if inventory.is_frozen:
        return jsonify(success=False, message='库存已冻结，禁止操作'), 400

    before = inventory.quantity

    # ====== 统一计算变动量 ======
    if action == 'in':
        change_qty = quantity
    elif action == 'out':
        change_qty = -quantity
    else:  # adjust
        change_qty = quantity  # 允许负数

    after = before + change_qty

    if after < 0:
        return jsonify(success=False, message='库存不足'), 400

    # ====== 更新库存 ======
    inventory.quantity = after

    # ====== 写库存流水 ======
    log = InventoryLog(
        inventory_id=inventory.id,
        company_id=inventory.company_id,
        user_id=g.current_user.id,
        action=action,
        change_quantity=change_qty,
        before_quantity=before,
        after_quantity=after,
        remark=remark
    )

    db.session.add(log)
    db.session.commit()

    return jsonify(success=True, data={'before_quantity': before, 'after_quantity': after})



# 库存流水
@inventory_bp.route('/inventory/logs', methods=['GET'])
@login_required
def inventory_logs():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 15, type=int)

    company_id = g.current_user.company_id

    # ====== 解析规格 change[xxx]=yyy ======
    change = {}
    for key, value in request.args.items():
        if key.startswith('change[') and key.endswith(']') and value:
            spec_code = key[7:-1]
            change[spec_code] = value

    # ====== 操作类型 ======
    action = request.args.get('action')
    if action not in ('in', 'out', 'adjust', None):
        return jsonify(success=False, message='非法操作类型'), 400

    # ====== 时间区间 ======
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # ====== 主查询（关键：company_id 过滤在 InventoryLog 上） ======
    query = (
        db.session.query(
            InventoryLog,
            Inventory,
            Product,
            User
        )
        .join(Inventory, InventoryLog.inventory_id == Inventory.id)
        .join(Product, Inventory.product_id == Product.id)
        .join(User, InventoryLog.user_id == User.id)
        .filter(InventoryLog.company_id == company_id)
    )

    # ====== 规格 JSON 过滤 ======
    for spec_code, spec_value in change.items():
        json_path = f'$."{spec_code}"'
        query = query.filter(
            func.JSON_UNQUOTE(
                func.JSON_EXTRACT(Product.spec_json, json_path)
            ) == spec_value
        )

    # ====== 操作类型过滤 ======
    if action:
        query = query.filter(InventoryLog.action == action)

    # ====== 时间区间过滤 ======
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(InventoryLog.created_at >= start_dt)
            query = query.filter(InventoryLog.created_at < end_dt)
        except ValueError:
            return jsonify(success=False, message='时间格式错误'), 400

    # ====== 排序 + 分页 ======
    query = query.order_by(InventoryLog.created_at.desc())
    pagination = query.paginate(
        page=page,
        per_page=page_size,
        error_out=False
    )

    # ====== 返回数据（统一 +8 小时） ======
    data = []
    for log, inventory, product, user in pagination.items:
        data.append({
            "id": log.id,
            "product_name": product.name,
            "action": log.action,
            "change_quantity": log.change_quantity,
            "before_quantity": log.before_quantity,
            "after_quantity": log.after_quantity,
            "operator_name": user.real_name,
            "remark": log.remark,
            "created_at": (
                log.created_at + timedelta(hours=8)
            ).strftime('%Y-%m-%d %H:%M:%S')
        })

    return jsonify(
        success=True,
        data=data,
        page=pagination.page,
        page_size=pagination.per_page,
        total=pagination.total
    )

# 创建盘点单与确认盘点单，没用到！！
# ==================================================
# 四、库存盘点（创建盘点单）
# ==================================================

@inventory_bp.route('/inventory/check', methods=['POST'])
def create_inventory_check():
    """
    创建库存盘点单
    只记录盘点结果，不调整库存
    """
    data = request.json
    company_id = g.current_user.company_id

    items = data.get('items', [])
    if not items:
        return jsonify(success=False, message='盘点明细不能为空')

    check = InventoryCheck(
        company_id=company_id,
        remark=data.get('remark')
    )
    db.session.add(check)
    db.session.flush()  # 拿到 check.id

    for item in items:
        inventory = Inventory.query.get_or_404(item['inventory_id'])

        # 防止跨厂区盘点
        if inventory.company_id != company_id:
            return jsonify(success=False, message='存在非法库存记录')

        system_qty = inventory.quantity
        actual_qty = int(item['actual_quantity'])

        check_item = InventoryCheckItem(
            check_id=check.id,
            inventory_id=inventory.id,
            system_quantity=system_qty,
            actual_quantity=actual_qty,
            difference=actual_qty - system_qty
        )
        db.session.add(check_item)

    db.session.commit()
    return jsonify(
        success=True,
        data={'check_id': check.id}
    )



# ==================================================
# 四、库存盘点（确认并调整库存）
# ==================================================

@inventory_bp.route('/inventory/check/confirm', methods=['POST'])
def confirm_inventory_check():
    """
    确认盘点单
    根据盘点差异生成库存调整流水
    """
    data = request.json
    user_id = g.current_user.id

    check = InventoryCheck.query.get_or_404(data['check_id'])

    if check.status != 'pending':
        return jsonify(success=False, message='盘点单状态不可确认')

    items = InventoryCheckItem.query.filter_by(check_id=check.id).all()

    for item in items:
        if item.difference == 0:
            continue

        inventory = Inventory.query.get_or_404(item.inventory_id)

        before_qty = inventory.quantity
        after_qty = item.actual_quantity

        # 更新库存
        inventory.quantity = after_qty

        # 写库存流水（唯一审计来源）
        log = InventoryLog(
            inventory_id=inventory.id,
            company_id=check.company_id,
            user_id=user_id,
            action='adjust',
            change_quantity=item.difference,
            before_quantity=before_qty,
            after_quantity=after_qty,
            remark='库存盘点调整'
        )
        db.session.add(log)

    check.status = 'confirmed'
    db.session.commit()

    return jsonify(success=True)

