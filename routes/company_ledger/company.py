from flask import Blueprint, request, jsonify
from db_config import db
from models import Company

company_bp = Blueprint('company', __name__)

# -------------------------------
# 序列化辅助函数
# -------------------------------
def company_to_dict(company: Company):
    """将 Company 对象转换为字典用于返回 JSON"""
    return {
        'id': company.id,
        'name': company.name,
        'description': company.description,
        'remark': company.remark
    }

# -------------------------------
# 创建公司
# -------------------------------
@company_bp.route('/create', methods=['POST'])
def create_company():
    """
    JSON 参数：
    - name: 公司名称（必填，唯一）
    - description: 公司描述，可选
    - remark: 备注，可选
    """
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    remark = data.get('remark', '')

    if not name:
        return jsonify({'success': False, 'message': '公司名称不能为空'}), 400

    # 检查公司名称唯一性
    if Company.query.filter_by(name=name).first():
        return jsonify({'success': False, 'message': '公司名称已存在'}), 400

    company = Company(name=name, description=description, remark=remark)
    db.session.add(company)
    db.session.commit()

    return jsonify({'success': True, 'data': company_to_dict(company)}), 201

# -------------------------------
# 获取公司列表
# -------------------------------
@company_bp.route('/list', methods=['GET'])
def list_companies():
    """
    可选查询参数：
    - name: 按公司名称模糊查询
    """
    name_filter = request.args.get('name')
    query = Company.query
    if name_filter:
        query = query.filter(Company.name.ilike(f'%{name_filter}%'))

    companies = query.all()
    return jsonify({'success': True, 'data': [company_to_dict(c) for c in companies]})

# -------------------------------
# 获取单个公司
# -------------------------------
@company_bp.route('/<int:company_id>', methods=['GET'])
def get_company(company_id):
    company = Company.query.get(company_id)
    if not company:
        return jsonify({'success': False, 'message': '公司不存在'}), 404
    return jsonify({'success': True, 'data': company_to_dict(company)})

# -------------------------------
# 更新公司
# -------------------------------
@company_bp.route('/<int:company_id>', methods=['PUT'])
def update_company(company_id):
    """
    JSON 参数：
    - name: 公司名称，可选
    - description: 公司描述，可选
    - remark: 备注，可选
    """
    company = Company.query.get(company_id)
    if not company:
        return jsonify({'success': False, 'message': '公司不存在'}), 404

    data = request.json
    name = data.get('name')
    description = data.get('description')
    remark = data.get('remark')

    if name:
        # 检查名称唯一性
        if Company.query.filter(Company.name == name, Company.id != company_id).first():
            return jsonify({'success': False, 'message': '公司名称已存在'}), 400
        company.name = name
    if description is not None:
        company.description = description
    if remark is not None:
        company.remark = remark

    db.session.commit()
    return jsonify({'success': True, 'data': company_to_dict(company)})

# -------------------------------
# 删除公司
# -------------------------------
@company_bp.route('/<int:company_id>', methods=['DELETE'])
def delete_company(company_id):
    """
    直接物理删除，实际业务中可改为软删除
    """
    company = Company.query.get(company_id)
    if not company:
        return jsonify({'success': False, 'message': '公司不存在'}), 404

    db.session.delete(company)
    db.session.commit()
    return jsonify({'success': True, 'message': '公司已删除'})
