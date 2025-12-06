from datetime import datetime
from flask import Blueprint, request, jsonify
from decimal import Decimal
from db_config import db
from models import Transaction, CustomerBalance, AdjustmentLog
from sqlalchemy import func


transaction_bp = Blueprint("transaction", __name__)


# 工具函数
def decimal2(val):
    return Decimal(str(val)).quantize(Decimal("0.01"))


# =============================
# 新增流水
# =============================
@transaction_bp.route("/add", methods=["POST"])
def add_transaction():
    data = request.json
    print("新增流水：", data)

    company_id = data.get("company_id")
    customer_id = data.get("customer_id")
    company_account_id = data.get("company_account_id")
    customer_account_id = data.get('customer_account_id')
    amount = decimal2(data.get("amount"))
    direction = data.get("direction")         # income / expense
    method = data.get("method")
    reference_no = data.get("reference_no")
    remark = data.get("remark")

    if not company_id or not customer_id or not company_account_id or not amount:
        return jsonify({"success": False, "message": "参数缺失"}), 400

    # 保存流水
    transaction = Transaction(
        company_id=company_id,
        customer_id=customer_id,
        company_account_id=company_account_id,
        customer_account_id=customer_account_id,
        amount=amount,
        direction=direction,
        method=method,
        reference_no=reference_no,
        remark=remark
    )
    db.session.add(transaction)

    # --- 更新客户欠款 ---
    cb = CustomerBalance.query.filter_by(
        customer_id=customer_id,
        company_id=company_id
    ).first()

    if not cb:
        cb = CustomerBalance(customer_id=customer_id, company_id=company_id, balance=0)
        db.session.add(cb)

    # income = 客户付款给公司  → 欠款减少
    # expense = 公司付款给客户 → 欠款增加
    if direction == "收入":
        cb.balance = decimal2(cb.balance - amount)
    else:
        cb.balance = decimal2(cb.balance + amount)

    db.session.commit()

    return jsonify({"success": True, "message": "新增流水成功"}), 200


# =============================
# 更新流水（不建议随便改金额）
# =============================
@transaction_bp.route("/update/<int:id>", methods=["PUT"])
def update_transaction(id):
    data = request.json
    item = Transaction.query.get(id)
    print('更新流水数据：',data)
    if not item:
        return jsonify({"success": False, "message": "记录不存在"}), 404

    # 只允许修改备注、方法、状态
    item.method = data.get("method", item.method)
    item.reference_no = data.get("reference_no", item.reference_no)
    item.remark = data.get("remark", item.remark)
    item.status = data.get("status", item.status)

    # 🔥 关键：更新时间
    item.updated_at = datetime.now()

    db.session.commit()

    return jsonify({"success": True, "message": "更新成功"})


# =============================
# 查询流水（可分页 + 条件）
# =============================
@transaction_bp.route("/list", methods=["GET"])
def list_transactions():
    company_id = request.args.get("company_id")
    customer_id = request.args.get("customer_id")
    direction = request.args.get("direction")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))

    query = Transaction.query.order_by(Transaction.created_at.desc())

    if company_id:
        query = query.filter(Transaction.company_id == company_id)
    if customer_id:
        query = query.filter(Transaction.customer_id == customer_id)
    if direction:
        query = query.filter(Transaction.direction == direction)

    # 时间范围（前端传 YYYY-MM-DD）
    if start_date and end_date:
        query = query.filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <  f"{end_date} 23:59:59"
        )

    # ⭐ 统计总金额（不分页）
    total_amount = query.with_entities(func.sum(Transaction.amount)).scalar() or 0

    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    records = []
    #print("流水分页记录：",pagination.items)
    for t in pagination.items:
        '''
        data = t.__dict__.copy()
        data.pop("_sa_instance_state", None)
        print("流水分页记录：", data)
        '''
        records.append({
            "id": t.id,
            "company_id": t.company_id,
            "customer_id": t.customer_id,
            "company_account_id": t.company_account_id,
            'customer_account_id': t.customer_account_id,
            "amount": float(t.amount),
            "direction": t.direction,
            "method": t.method,
            "reference_no": t.reference_no,
            "status": t.status,
            "remark": t.remark,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": t.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify({
        "success": True,
        "data": records,
        "total": pagination.total,
        "total_amount": float(total_amount)    # ⭐ 返回给前端
    })


# =============================
# 删除流水
# =============================
@transaction_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_transaction(id):
    item = Transaction.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "记录不存在"}), 404

    # 删除对客户欠款的影响
    cb = CustomerBalance.query.filter_by(
        customer_id=item.customer_id, company_id=item.company_id
    ).first()

    if cb:
        amount = item.amount

        # income = 客户付款 → 欠款减少
        # 删除收入流水 = 欠款增加
        if item.direction == "收入":
            cb.balance = decimal2(cb.balance + amount)
        else:
            cb.balance = decimal2(cb.balance - amount)

    db.session.delete(item)
    db.session.commit()

    return jsonify({"success": True, "message": "删除成功"})
