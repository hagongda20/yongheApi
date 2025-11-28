from flask import Blueprint, request, jsonify
from db_config import db
from models import WageLog
from utils.decorators import login_required
from datetime import datetime
import pytz

wage_log_bp = Blueprint('wage_log', __name__)

utc = pytz.utc
china = pytz.timezone('Asia/Shanghai')

# 创建工资记录
@wage_log_bp.route('/', methods=['POST'])
@login_required
def add_wage_log(current_user):
    data = request.get_json()
    print("data:",data)
    required_fields = ['actual_price', 'quantity', 'total_wage','actual_group_size', 'worker_id', 'process_id', 'spec_model_id']
    if not all(field in data for field in required_fields):
        return jsonify({'ok': False, 'msg': '缺少字段'}), 400

    new_log = WageLog(
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        actual_price=data['actual_price'],
        quantity=data['quantity'],
        actual_group_size=data['actual_group_size'],
        total_wage=data['total_wage'],
        remark=data.get('remark', ''),
        worker_id=data['worker_id'],
        process_id=data['process_id'],
        spec_model_id=data['spec_model_id'],
    )
    db.session.add(new_log)
    db.session.commit()

    return jsonify({'ok': True, 'msg': '日薪记录成功', 'data': new_log.to_dict()}), 201

# 删除工资记录
@wage_log_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_wage_log(id, current_user):
    log = WageLog.query.get(id)
    if not log:
        return jsonify({'ok': False, 'msg': '工资信息不存在'}), 404

    db.session.delete(log)
    db.session.commit()
    return jsonify({'ok': True, 'msg': '工资记录删除成功'}), 200

# 更新工资记录
@wage_log_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_wage_log(id, current_user):
    log = WageLog.query.get(id)
    if not log:
        return jsonify({'ok': False, 'msg': '工资信息不存在'}), 404

    data = request.get_json()

    if 'date' in data:
        log.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    log.actual_price = data.get('actual_price', log.actual_price)
    log.quantity = data.get('quantity', log.quantity)
    log.actual_group_size = data.get('actual_group_size', log.actual_group_size)
    log.total_wage = data.get('total_wage', log.total_wage)
    log.remark = data.get('remark', log.remark)

    log.worker_id = data.get('worker_id', log.worker_id)
    log.process_id = data.get('process_id', log.process_id)
    log.spec_model_id = data.get('spec_model_id', log.spec_model_id)

    db.session.commit()
    return jsonify({'ok': True, 'msg': '工资记录更新成功'}), 200

# 获取单条工资记录
@wage_log_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_wage_log(id, current_user):
    wage_log = WageLog.query.get(id)
    if not wage_log:
        return jsonify({'ok': False, 'msg': '工资信息不存在'}), 404

    return jsonify({'ok': True, 'msg': '查询成功', 'data': wage_log.to_dict(relations=['process', 'spec_model'])}), 200

# 获取所有工资记录
@wage_log_bp.route('/', methods=['GET'])
@login_required
def get_wage_logs(current_user):
    date_str = request.args.get('date')  # 获取查询参数中的日期
    if date_str:
        try:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'ok': False, 'msg': '日期格式错误. 请使用 YYYY-MM-DD.'}), 400

        logs = WageLog.query.filter_by(date=query_date).all()
    else:
        logs = WageLog.query.all()

    log_list = [log.to_dict(relations=['worker', 'process', 'spec_model']) for log in logs]
    return jsonify({'ok': True, 'msg': '查询成功', 'data': log_list}), 200

# 日期区间、工人、工序综合查询
@wage_log_bp.route('/query', methods=['GET'])
@login_required
def query_wage_logs(current_user):
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    worker_id = request.args.get('worker_id')
    process_id = request.args.get('process_id')

    query = WageLog.query

    # 日期区间过滤
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        query = query.filter(WageLog.date >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        query = query.filter(WageLog.date <= end_date)

    # 工人过滤
    if worker_id:
        query = query.filter(WageLog.worker_id == worker_id)
    # 工序过滤
    if process_id:
        query = query.filter(WageLog.process_id == process_id)

    logs = query.order_by(WageLog.date, WageLog.process_id, WageLog.spec_model_id).all()
    log_list = [log.to_dict(relations=['worker', 'process', 'spec_model']) for log in logs]
    return jsonify({'ok': True, 'msg':'查询成功', 'data': log_list}), 200

# 批量导入工资记录
@wage_log_bp.route('/batch_import', methods=['POST'])
@login_required
def batch_import_wage_logs(current_user):
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({'ok': False, 'message': '数据格式错误，需为数组'}), 400

    batch_size = 500  # 每次插入数量，防止一次插入过大
    total = len(data)
    inserted_count = 0
    print("准备批量导入的数据：", data)
    for i in range(0, total, batch_size):
        chunk = data[i:i+batch_size]
        wage_objs = []

        for row in chunk:
            # 必填字段检查
            required_fields = ['actual_price', 'quantity', 'total_wage', 'actual_group_size', 'worker_id', 'process_id','spec_model_id']
            if not all(field in row for field in required_fields):
                continue  # 跳过缺失字段的行
            # 构建 WageLog 对象
            wage = WageLog(
                date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                actual_price=row['actual_price'],
                quantity=row['quantity'],
                actual_group_size=row.get('actual_group_size', 1),
                total_wage=row['total_wage'],

                worker_id=row['worker_id'],
                process_id=row['process_id'],
                spec_model_id=row['spec_model_id'],
            )
            wage_objs.append(wage)

        # 批量写入
        if wage_objs:
            db.session.bulk_save_objects(wage_objs)
            db.session.commit()
            inserted_count += len(wage_objs)

    return jsonify({'ok': True,'msg': '导入成功','data': {'total': total, 'inserted_count': inserted_count}}), 200
