from flask import Blueprint, request, jsonify
from db_config import db
from models import Process
from utils.decorators import login_required

process_bp = Blueprint('process', __name__)

# 获取所有工序
@process_bp.route('/', methods=['GET'])
@login_required
def get_processes():
    try:
        processes = Process.query.all()
        process_list = [
            {
                'id': p.id,
                'name': p.name,
                'description': p.description
            } for p in processes
        ]
        return jsonify({'processes': process_list}), 200
    except Exception as e:
        print(f"Error fetching processes: {e}")
        return jsonify({'message': 'Failed to fetch processes', 'error': str(e)}), 400


# 获取单个工序
@process_bp.route('/<int:id>', methods=['GET'])
def get_process(id):
    process = Process.query.get(id)
    if not process:
        return jsonify({'message': 'Process not found'}), 404
    return jsonify({
        'id': process.id,
        'name': process.name,
        'description': process.description
    }), 200


# 创建工序
@process_bp.route('/', methods=['POST'])
def add_process():
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'message': 'Name is required'}), 400

    try:
        new_process = Process(
            name=data['name'],
            description=data.get('description', '')
        )
        db.session.add(new_process)
        db.session.commit()

        return jsonify({
            'message': 'Process created successfully',
            'process': {
                'id': new_process.id,
                'name': new_process.name
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400


# 更新工序
@process_bp.route('/<int:id>', methods=['PUT'])
def update_process(id):
    process = Process.query.get(id)
    if not process:
        return jsonify({'message': 'Process not found'}), 404

    data = request.get_json()
    process.name = data.get('name', process.name)
    process.description = data.get('description', process.description)

    try:
        db.session.commit()
        return jsonify({
            'message': 'Process updated successfully',
            'process': {
                'id': process.id,
                'name': process.name
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400


# 删除工序
@process_bp.route('/<int:id>', methods=['DELETE'])
def delete_process(id):
    process = Process.query.get(id)
    if not process:
        return jsonify({'message': 'Process not found'}), 404

    try:
        db.session.delete(process)
        db.session.commit()
        return jsonify({'message': 'Process deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400
