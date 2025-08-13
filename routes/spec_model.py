from flask import Blueprint, request, jsonify
from db_config import db
from models import SpecModel
from utils.decorators import login_required

spec_model_bp = Blueprint('spec_model', __name__, url_prefix='/api/specmodels')


# 获取所有规格型号
@spec_model_bp.route('/', methods=['GET'])
@login_required
def get_spec_models():
    try:
        spec_models = SpecModel.query.order_by(SpecModel.process_id).all()
        result = [
            {
                'id': s.id,
                'name': s.name,
                'category': s.category,
                'process_id': s.process_id,
                'process_name':s.process.name,
                'price': s.price
            } for s in spec_models
        ]
        return jsonify({'specModels': result}), 200
    except Exception as e:
        print(f"Error fetching spec models: {e}")
        return jsonify({'message': 'Failed to fetch spec models', 'error': str(e)}), 400


# 获取单个规格型号
@spec_model_bp.route('/<int:id>', methods=['GET'])
def get_spec_model(id):
    spec = SpecModel.query.get(id)
    if not spec:
        return jsonify({'message': 'Spec model not found'}), 404
    return jsonify({
        'id': spec.id,
        'name': spec.name,
        'category': spec.category,
        'process_id': spec.process_id,
        'price': spec.price
    }), 200


# 创建规格型号
@spec_model_bp.route('/', methods=['POST'])
def add_spec_model():
    data = request.get_json()
    print("创建规格型号：",data)
    if not data.get('name') or not data.get('category') or not data.get('process_id'):
        return jsonify({'message': 'Name, category, and process_id are required'}), 400

    try:
        new_spec = SpecModel(
            name=data['name'],
            category=data['category'],
            process_id=data['process_id'],
            price = data['price']
        )
        db.session.add(new_spec)
        db.session.commit()
        return jsonify({
            'message': 'Spec model created successfully',
            'specModel': {
                'id': new_spec.id,
                'name': new_spec.name,
                'category': new_spec.category,
                'process_id': new_spec.process_id,
                'price': new_spec.price
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400


# 更新规格型号
@spec_model_bp.route('/<int:id>', methods=['PUT'])
def update_spec_model(id):
    spec = SpecModel.query.get(id)
    if not spec:
        return jsonify({'message': 'Spec model not found'}), 404

    data = request.get_json()
    spec.name = data.get('name', spec.name)
    spec.category = data.get('category', spec.category)
    spec.process_id = data.get('process_id', spec.process_id)
    spec.price = data.get('price', spec.price)

    try:
        db.session.commit()
        return jsonify({
            'message': 'Spec model updated successfully',
            'specModel': {
                'id': spec.id,
                'name': spec.name,
                'category': spec.category,
                'process_id': spec.process_id,
                'price': spec.price
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400


# 删除规格型号
@spec_model_bp.route('/<int:id>', methods=['DELETE'])
def delete_spec_model(id):
    spec = SpecModel.query.get(id)
    print("删除的规格型号：", spec.id,spec.name,spec.price)
    if not spec:
        return jsonify({'message': 'Spec model not found'}), 404

    try:
        db.session.delete(spec)
        db.session.commit()
        return jsonify({'message': 'Spec model deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

# 获取指定工序下的所有规格型号
@spec_model_bp.route('/by_process/<int:process_id>', methods=['GET'])
def get_spec_models_by_process(process_id):
    spec_models = SpecModel.query.filter_by(process_id=process_id).all()
    result = [sm.to_dict() for sm in spec_models]
    return jsonify({'spec_models': result}), 200

