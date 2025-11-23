from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from db_config import db
from models import Worker,Process
from utils.decorators import login_required
import pytz

worker_bp = Blueprint('worker', __name__)
china = pytz.timezone('Asia/Shanghai')

# 新增工人
@worker_bp.route('/', methods=['POST'])
@login_required
def add_worker(current_user):
    data = request.get_json()
    # 基本数据验证
    if not data:
        return jsonify({'ok': False, 'msg': '缺少请求数据'}), 400

    if not data.get('name') or not data.get('process_id'):
        return jsonify({'ok': False, 'msg': '姓名和工序ID不能为空'}), 400

    try:
        process_id = int(data['process_id'])
    except (ValueError, TypeError):
        return jsonify({'ok': False, 'msg': 'process_id 必须是有效整数'}), 400

    process = Process.query.get(process_id)
    if not process:
        return jsonify({'message': '指定的工序不存在'}), 400

    if Worker.query.filter_by(id_card=data.get('id_card')).first():
        return jsonify({'ok': False, 'msg': '工人身份证号重复'}), 400

    # 创建新工人
    new_worker = Worker(
        name=data['name'],
        id_card=data.get('id_card', ''),
        group=data.get('group', ''),
        entry_date=data.get('entry_date', ''),
        leave_date=data.get('leave_date', ''),
        status=data.get('status', ''),
        remark=data.get('remark', ''),
        process_id=process_id
    )

    db.session.add(new_worker)
    db.session.commit()

    return jsonify({
        "ok": True,
        'msg': '工人创建成功',
        'data': {
            'id': new_worker.id,
            'name': new_worker.name
        }
    }), 201


# 删除工人
@worker_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_worker(id, current_user):
    worker = Worker.query.get(id)

    if worker is None:
        return jsonify({'ok': False, 'msg': '工人不存在'}), 404
    db.session.delete(worker)
    db.session.commit()
    return jsonify({'ok': True, 'msg': '工人删除成功'}), 200



# 更新工人信息
@worker_bp.route('/<int:id>', methods=['PUT'])
def update_worker(id):
    worker = Worker.query.get(id)

    if worker is None:
        return jsonify({'ok': False, 'msg': '工人不存在'}), 404

    data = request.get_json()
    # 更新工人信息
    worker.name = data.get('name', worker.name)
    worker.id_card = data.get('id_card', worker.id_card)
    worker.group = data.get('group', worker.group)
    worker.entry_date = data.get('entry_date', worker.entry_date)
    worker.leave_date = data.get('leave_date', worker.leave_date)
    worker.status = data.get('status', worker.status)
    worker.process_id = data.get('process_id', worker.process_id)
    worker.remark = data.get('remark', worker.remark)

    db.session.commit()
    return jsonify({
        'ok': True,
        'msg': '工人信息更新成功',
        'data': {
            'id': worker.id,
            'name': worker.name
        }
    }), 200


# 获取单个工人详情
@worker_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_worker(id, current_user):
    worker = Worker.query.get(id)
    if worker is None:
        return jsonify({'ok': False, 'msg': '工人不存在'}), 404

    return jsonify({
        'ok' : True,
        'msg': '查找成功',
        'data' : {
            'id': worker.id,
            'name': worker.name,
            'id_card': worker.id_card,
            'group': worker.group,
            'process_id': worker.process_id,
            'entry_date': worker.entry_date.strftime('%Y-%m-%d'),
            'leave_date': worker.leave_date.strftime('%Y-%m-%d') if worker.leave_date else None,
            'status': worker.status,
            'remark': worker.remark,
        }
    }), 200

# 工人列表
@worker_bp.route('/', methods=['GET'])
@login_required
def get_workers(current_user):
    # 查询所有工人数据
    date_str = request.args.get('date')  # 获取查询参数中的日期

    if date_str:
        try:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'ok': False, 'msg': '日期格式错误. 请使用 YYYY-MM-DD.'}), 400

        workers = Worker.query.filter(
            Worker.entry_date <= query_date,
            or_(Worker.leave_date.is_(None), Worker.leave_date >= query_date)
        ).all()
    else:
        workers = Worker.query.all()
    # 构造返回的数据
    worker_list = [
        {
            'id': worker.id,
            'name': worker.name,
            'id_card': worker.id_card,
            'remark': worker.remark,
            'group': worker.group,
            'entry_date': worker.entry_date.strftime('%Y-%m-%d'),
            'leave_date': worker.leave_date.strftime('%Y-%m-%d') if worker.leave_date else None,
            'status': worker.status,
            'process': {
                'id': worker.process.id,
                'name': worker.process.name
            } if worker.process else None
        }
        for worker in workers
    ]
    return jsonify({'ok': True, 'msg': '获取成功', 'data': worker_list}), 200

