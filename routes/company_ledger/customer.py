# routes/customer/customer.py
from flask import Blueprint, request, jsonify
from db_config import db
from models import Customer

customer_bp = Blueprint('customer', __name__)


# -------------------------------
# 获取客户列表（支持分页和搜索）
# -------------------------------
@customer_bp.route('/', methods=['GET'])
def get_customers():
    """
    查询客户列表
    支持参数：
    - page: 页码，默认1
    - per_page: 每页条数，默认20
    - name: 客户名称模糊搜索
    - type: 客户类型（supplier/sales/other）
    """
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    name = request.args.get('name')
    cust_type = request.args.get('type')

    query = Customer.query.filter_by(is_deleted=False)

    if name:
        query = query.filter(Customer.name.ilike(f'%{name}%'))
    if cust_type:
        query = query.filter_by(type=cust_type)

    pagination = query.order_by(Customer.id.desc()).paginate(page=page, per_page=per_page)
    data = []
    for cust in pagination.items:
        data.append({
            'id': cust.id,
            'name': cust.name,
            'type': cust.type,
            'phone': cust.phone,
            'company': cust.company,
            'remark': getattr(cust, 'remark', '')
        })

    return jsonify({
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'items': data
    })


# -------------------------------
# 获取单个客户
# -------------------------------
@customer_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    cust = Customer.query.get_or_404(customer_id)
    if cust.is_deleted:
        return jsonify({'error': '客户已删除'}), 404
    return jsonify({
        'id': cust.id,
        'name': cust.name,
        'type': cust.type,
        'phone': cust.phone,
        'company': cust.company,
        'remark': getattr(cust, 'remark', '')
    })


# -------------------------------
# 新增客户
# -------------------------------
@customer_bp.route('/', methods=['POST'])
def add_customer():
    data = request.json
    name = data.get('name')
    cust_type = data.get('type')
    phone = data.get('phone')
    company_name = data.get('company')
    remark = data.get('remark', '')

    if not name or not cust_type:
        return jsonify({'error': '客户名称和类型必填'}), 400

    cust = Customer(
        name=name,
        type=cust_type,
        phone=phone,
        company=company_name,
        remark=remark
    )
    db.session.add(cust)
    db.session.commit()
    return jsonify({'message': '客户创建成功', 'id': cust.id})


# -------------------------------
# 更新客户
# -------------------------------
@customer_bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    cust = Customer.query.get_or_404(customer_id)
    if cust.is_deleted:
        return jsonify({'error': '客户已删除'}), 404

    data = request.json
    cust.name = data.get('name', cust.name)
    cust.type = data.get('type', cust.type)
    cust.phone = data.get('phone', cust.phone)
    cust.company = data.get('company', cust.company)
    cust.remark = data.get('remark', getattr(cust, 'remark', ''))

    db.session.commit()
    return jsonify({'message': '客户更新成功'})


# -------------------------------
# 删除客户（软删除）
# -------------------------------
@customer_bp.route('/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    cust = Customer.query.get_or_404(customer_id)
    if cust.is_deleted:
        return jsonify({'error': '客户已删除'}), 404

    cust.is_deleted = True
    from datetime import datetime
    cust.deleted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': '客户已软删除'})
