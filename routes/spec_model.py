from flask import Blueprint, request, jsonify
from db_config import db
from models import SpecModel
from utils.decorators import login_required

spec_model_bp = Blueprint('spec_model', __name__, url_prefix='/api/specmodels')

# 创建规格型号
@spec_model_bp.route('/', methods=['POST'])
@login_required
def add_spec_model(current_user):
    data = request.get_json()
    if not data.get('name') or not data.get('category') or not data.get('process_id') or not data.get('price'):
        return jsonify({'ok': False, 'msg': '缺少字段：规格名称, 分类, 工序ID'}), 400

    new_spec = SpecModel(
        name=data['name'],
        category=data['category'],
        process_id=data['process_id'],
        price=data['price']
    )
    db.session.add(new_spec)
    db.session.commit()
    return jsonify({ 'ok': True, 'msg': '规格型号创建成功', 'data': new_spec.to_dict() }), 201

# 删除规格型号
@spec_model_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_spec_model(id, current_user):
    spec = SpecModel.query.get(id)
    if not spec:
        return jsonify({'ok': False, 'msg': '规格型号不存在'}), 404

    db.session.delete(spec)
    db.session.commit()
    return jsonify({'ok': True, 'msg': '规格型号删除成功'}), 200

# 更新规格型号
@spec_model_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_spec_model(id, current_user):
    spec = SpecModel.query.get(id)
    if not spec:
        return jsonify({'ok': False, 'msg': '规格型号不存在'}), 404

    data = request.get_json()
    spec.name = data.get('name', spec.name)
    spec.category = data.get('category', spec.category)
    spec.process_id = data.get('process_id', spec.process_id)
    spec.price = data.get('price', spec.price)

    db.session.commit()
    return jsonify({'ok': True, 'msg': '规格型号更新成功'}), 200


# 获取单个规格型号
@spec_model_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_spec_model(id, current_user):
    spec = SpecModel.query.get(id)
    if not spec:
        return jsonify({'msg': '规格型号不存在'}), 404
    return jsonify({'ok': True, 'msg': '规格型号查找成功', 'data': spec.to_dict(relations=['process'])}), 200

# 获取所有规格型号
@spec_model_bp.route('/', methods=['GET'])
@login_required
def get_spec_models(current_user):
    spec_models = SpecModel.query.order_by(SpecModel.process_id).all()
    result = [s.to_dict(relations=['process']) for s in spec_models]
    return jsonify({'ok': True, 'msg': '获取所有规格型号成功', 'data': result}), 200

# 获取指定工序下的所有规格型号
@spec_model_bp.route('/by_process/<int:process_id>', methods=['GET'])
@login_required
def get_spec_models_by_process(process_id, current_user):
    spec_models = SpecModel.query.filter_by(process_id=process_id).all()
    result = [sm.to_dict(relations=['process']) for sm in spec_models]
    return jsonify({'ok': True, 'msg': '规格型号创建成功', 'data': result}), 200