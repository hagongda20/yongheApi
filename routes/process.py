from flask import Blueprint, request, jsonify
from db_config import db
from models import Process
from utils.decorators import login_required

process_bp = Blueprint('process', __name__)

# 创建工序
@process_bp.route('/', methods=['POST'])
@login_required
def add_process(current_user):
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'ok': False, 'msg': '工序名称不可为空'}), 400

    if Process.query.filter_by(name=data.get('name')).first():
        return jsonify({'ok': False, 'msg': '工序已经存在'}), 400

    new_process = Process(
        name=data['name'],
        description=data.get('description', '')
    )
    db.session.add(new_process)
    db.session.commit()

    return jsonify({
        'ok': True,
        'msg': '工序创建成功',
        'data': {
            'id': new_process.id,
            'name': new_process.name
        }
    }), 201


# 删除工序
@process_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_process(id, current_user):
    process = Process.query.get(id)
    if not process:
        return jsonify({'ok': False, 'msg': '工序不存在'}), 404

    db.session.delete(process)
    db.session.commit()
    return jsonify({'ok': True, 'msg': '工序删除成功'}), 200

# 更新工序
@process_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_process(id, current_user):
    process = Process.query.get(id)
    if not process:
        return jsonify({'ok': False, 'msg': '工序不存在'}), 404

    data = request.get_json()
    process.name = data.get('name', process.name)
    process.description = data.get('description', process.description)

    db.session.commit()
    return jsonify({
        'ok': True,
        'msg': '工序更新成功',
        'data': {
            'id': process.id,
            'name': process.name
        }
    }), 200

# 获取单个工序
@process_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_process(id, current_user):
    process = Process.query.get(id)
    if not process:
        return jsonify({'ok': False, 'msg': '工序不存在'}), 404
    return jsonify({
        'ok': True,
        'msg': '查询成功',
        'data': {
            'id': process.id,
            'name': process.name,
            'description': process.description
        }
    }), 200


# 获取所有工序
@process_bp.route('/', methods=['GET'])
@login_required
def get_processes(current_user):
    processes = Process.query.all()
    process_list = [
        {
            'id': p.id,
            'name': p.name,
            'description': p.description
        } for p in processes
    ]
    return jsonify({ 'ok': True, 'msg': '查询成功', 'data': process_list }), 200

