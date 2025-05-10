from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from db_config import db
from models import Worker,Process
import pytz

worker_bp = Blueprint('worker', __name__)

utc = pytz.utc
china = pytz.timezone('Asia/Shanghai')

# 工人列表
@worker_bp.route('/', methods=['GET'])
def get_workers():
    try:
        # 查询所有工人数据
        date_str = request.args.get('date')  # 获取查询参数中的日期

        if date_str:
            try:
                query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400

            workers = Worker.query.filter(
                Worker.entry_date <= query_date,
                or_(Worker.leave_date.is_(None), Worker.leave_date >= query_date)
            ).all()

        else:
            workers = Worker.query.all()
        #workers = Worker.query.all()
        #print("所有工人：", workers)
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
        print("序列化工人列表:",worker_list)
        return jsonify({'workers': worker_list}), 200
    except Exception as e:
        # 记录详细错误信息
        print(f"Error occurred: {e}")
        return jsonify({'message': 'Failed to fetch workers', 'error': str(e)}), 400


# 获取单个工人详情
@worker_bp.route('/<int:id>', methods=['GET'])
def get_worker(id):
    worker = Worker.query.get(id)
    if worker is None:
        return jsonify({'message': 'Worker not found'}), 404

    return jsonify({
        'id': worker.id,
        'name': worker.name,
        'id_card': worker.id_card,
        'remark': worker.remark,
        'group': worker.group,
        'process_id': worker.process_id,
        'entry_date': worker.entry_date.strftime('%Y-%m-%d'),
        'leave_date': worker.leave_date.strftime('%Y-%m-%d') if worker.leave_date else None,
        'status': worker.status,
    }), 200


# 新增工人
@worker_bp.route('/', methods=['POST'])
def add_worker():
    print("接受 POST 数据")
    data = request.get_json()
    print("Received data:", data)

    # 基本数据验证
    if not data:
        return jsonify({'message': '缺少请求数据'}), 400

    if not data.get('name') or not data.get('process_id'):
        return jsonify({'message': '姓名和工序ID不能为空'}), 400

    # 将 process_id 强制转换为整数，防止类型错误
    try:
        process_id = int(data['process_id'])
    except (ValueError, TypeError):
        return jsonify({'message': 'process_id 必须是有效整数'}), 400

    try:
        # 检查工序是否存在（可选，但更严谨）
        process = Process.query.get(process_id)
        if not process:
            return jsonify({'message': '指定的工序不存在'}), 400

        # 创建新工人
        new_worker = Worker(
            name=data['name'],
            id_card=data.get('id_card', ''),
            remark=data.get('remark', ''),
            group=data.get('group', ''),
            entry_date=data.get('entry_date', ''),
            leave_date=data.get('leave_date', ''),
            status=data.get('status', ''),
            process_id=process_id
        )

        db.session.add(new_worker)
        db.session.commit()

        return jsonify({
            'message': '工人创建成功',
            'worker': {
                'id': new_worker.id,
                'name': new_worker.name
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error occurred: {e}")
        return jsonify({'message': '创建工人失败', 'error': str(e)}), 400



# 更新工人信息
@worker_bp.route('/<int:id>', methods=['PUT'])
def update_worker(id):
    worker = Worker.query.get(id)

    if worker is None:
        return jsonify({'message': 'Worker not found'}), 404

    data = request.get_json()

    # 更新工人信息
    worker.name = data.get('name', worker.name)
    worker.id_card = data.get('id_card', worker.id_card)
    worker.remark = data.get('remark', worker.remark)
    worker.group = data.get('group', worker.group)
    worker.entry_date = data.get('entry_date', worker.entry_date)
    worker.leave_date = data.get('leave_date', worker.leave_date)
    worker.status = data.get('status', worker.status)
    worker.process_id = data.get('process_id', worker.process_id)

    try:
        db.session.commit()
        return jsonify({
            'message': 'Worker updated successfully',
            'worker': {
                'id': worker.id,
                'name': worker.name
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400


# 删除工人
@worker_bp.route('/<int:id>', methods=['DELETE'])
def delete_worker(id):
    worker = Worker.query.get(id)

    if worker is None:
        return jsonify({'message': 'Worker not found'}), 404

    try:
        db.session.delete(worker)
        db.session.commit()
        return jsonify({'message': 'Worker deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400
