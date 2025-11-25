from flask import Blueprint, request, jsonify
from db_config import db
from models import Process, Worker
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
    print(process.to_dict(relations=['workers', 'spec_models', 'wage_logs']))
    return jsonify({'ok': True, 'msg': '查询成功', 'data': process.to_dict(relations=['workers', 'spec_models', 'wage_logs'])}), 200

# 获取所有工序
@process_bp.route('/', methods=['GET'])
@login_required
def get_processes(current_user):
    worker_id = request.args.get('worker_id')

    if worker_id:
        # 根据 worker_id 查询该工人所属的工序
        worker = Worker.query.get(worker_id)
        if not worker:
            return jsonify({'ok': False, 'msg': '工人不存在'}), 404

        # 返回该工人对应的工序
        process = Process.query.get(worker.process_id)
        if process:
            process_list = [process.to_dict()]
        else:
            process_list = []
    else:
        # 没有 worker_id 参数时返回所有工序
        processes = Process.query.all()
        process_list = [p.to_dict(relations=['workers', 'spec_models', 'wage_logs']) for p in processes]

    return jsonify({'ok': True, 'msg': '查询成功', 'data': process_list}), 200

