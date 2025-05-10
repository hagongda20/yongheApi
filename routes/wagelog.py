from flask import Blueprint, request, jsonify
from db_config import db
from models import WageLog, Worker, Process, SpecModel
from datetime import datetime
import pytz

wagelog_bp = Blueprint('wagelog', __name__)

utc = pytz.utc
china = pytz.timezone('Asia/Shanghai')

# 获取所有工资记录
@wagelog_bp.route('/', methods=['GET'])
def get_wage_logs():
    try:
        date_str = request.args.get('date')  # 获取查询参数中的日期

        if date_str:
            try:
                query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400

            logs = WageLog.query.filter_by(date=query_date).all()
        else:
            logs = WageLog.query.all()

        # print('工资记录：', logs)

        log_list = [
            {
                'id': log.id,
                'worker_id': log.worker_id,
                'worker': log.worker.name if log.worker else None,
                'process_id': log.process_id,
                # 'process': log.process.name if log.process else None,
                'spec_model_id': log.spec_model_id,
                # 'spec_model': log.spec_model.name if log.spec_model else None,
                'date': log.date.strftime('%Y-%m-%d'),
                'actual_price': float(log.actual_price),
                'actual_group_size': log.actual_group_size,
                'quantity': log.quantity,
                'total_wage': float(log.total_wage),
                'remark': log.remark,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': log.updated_at.strftime('%Y-%m-%d %H:%M')
            } for log in logs
        ]
        return jsonify({'wage_logs': log_list}), 200
    except Exception as e:
        print(f"Error fetching wage logs: {e}")
        return jsonify({'message': 'Failed to fetch wage logs', 'error': str(e)}), 400



# 获取单条工资记录
@wagelog_bp.route('/<int:id>', methods=['GET'])
def get_wage_log(id):
    log = WageLog.query.get(id)
    if not log:
        return jsonify({'message': 'Wage log not found'}), 404

    created_at_utc = utc.localize(log.created_at)
    updated_at_utc = utc.localize(log.updated_at)

    return jsonify({
        'id': log.id,
        'worker_id': log.worker_id,
        'worker': log.worker.name if log.worker else None,
        'process_id': log.process_id,
        'process': log.process.name if log.process else None,
        'spec_model_id': log.spec_model_id,
        'spec_model': log.spec_model.name if log.spec_model else None,
        'date': log.date.strftime('%Y-%m-%d'),
        'actual_price': float(log.actual_price),
        'actual_group_size': log.actual_group_size,
        'quantity': log.quantity,
        'total_wage': float(log.total_wage),
        'remark': log.remark,
        'created_at': created_at_utc.astimezone(china).strftime('%Y-%m-%d %H:%M'),
        'updated_at': updated_at_utc.astimezone(china).strftime('%Y-%m-%d %H:%M')
    }), 200


# 创建工资记录
@wagelog_bp.route('/', methods=['POST'])
def add_wage_log():
    data = request.get_json()
    print("data:",data)
    required_fields = ['worker_id', 'process_id', 'spec_model_id', 'actual_price', 'quantity', 'total_wage']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        new_log = WageLog(
            worker_id=data['worker_id'],
            process_id=data['process_id'],
            spec_model_id=data['spec_model_id'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            actual_price=data['actual_price'],
            actual_group_size=data['actual_group_size'],
            quantity=data['quantity'],
            total_wage=data['total_wage'],
            remark=data.get('remark', '')
        )
        db.session.add(new_log)
        db.session.commit()

        return jsonify({'message': 'Wage log created successfully', 'id': new_log.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400


# 更新工资记录
@wagelog_bp.route('/<int:id>', methods=['PUT'])
def update_wage_log(id):
    log = WageLog.query.get(id)
    if not log:
        return jsonify({'message': 'Wage log not found'}), 404

    data = request.get_json()
    try:
        log.worker_id = data.get('worker_id', log.worker_id)
        log.process_id = data.get('process_id', log.process_id)
        log.spec_model_id = data.get('spec_model_id', log.spec_model_id)
        if 'date' in data:
            log.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        log.actual_price = data.get('actual_price', log.actual_price)
        log.actual_group_size = data.get('actual_group_size', log.actual_group_size)
        log.quantity = data.get('quantity', log.quantity)
        log.total_wage = data.get('total_wage', log.total_wage)
        log.remark = data.get('remark', log.remark)
        

        db.session.commit()
        return jsonify({'message': 'Wage log updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400


# 删除工资记录
@wagelog_bp.route('/<int:id>', methods=['DELETE'])
def delete_wage_log(id):
    log = WageLog.query.get(id)
    if not log:
        return jsonify({'message': 'Wage log not found'}), 404

    try:
        db.session.delete(log)
        db.session.commit()
        return jsonify({'message': 'Wage log deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

# 日期区间、工人、工序综合查询
@wagelog_bp.route('/query', methods=['GET'])
def query_wage_logs():
    try:
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

        # 工人姓名模糊查询
        if worker_id:
            # query = query.join(Worker).filter(Worker.name.ilike(f'%{worker_name}%'))
            query = query.filter(WageLog.worker_id == worker_id)
        # 工序过滤
        if process_id:
            query = query.filter(WageLog.process_id == process_id)

        #logs = query.all()
        logs = query.order_by(WageLog.date, WageLog.process_id, WageLog.spec_model_id).all()

        log_list = [
            {
                'id': log.id,
                'worker_id': log.worker_id,
                'worker': log.worker.name if log.worker else None,
                'process_id': log.process_id,
                'process': log.process.name if log.process else None,
                'spec_model_id': log.spec_model_id,
                'spec_model': log.spec_model.name if log.spec_model else None,
                'date': log.date.strftime('%Y-%m-%d'),
                'actual_price': float(log.actual_price),
                'actual_group_size': log.actual_group_size,
                'quantity': log.quantity,
                'total_wage': float(log.total_wage),
                'remark': log.remark,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': log.updated_at.strftime('%Y-%m-%d %H:%M')
            } for log in logs
        ]
        print("综合查询:", log_list)
        return jsonify({'wage_logs': log_list}), 200

    except Exception as e:
        print(f"Error querying wage logs: {e}")
        return jsonify({'message': 'Failed to query wage logs', 'error': str(e)}), 400

