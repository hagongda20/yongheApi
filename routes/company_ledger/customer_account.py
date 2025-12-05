from flask import Blueprint, request, jsonify
from db_config import db
from models import CustomerAccount
from datetime import datetime

customer_account_bp = Blueprint("customer_account_bp", __name__)


# -------------------------------------------------
# 新增客户支付账户
# -------------------------------------------------
@customer_account_bp.post("/add")
def add_account():
    data = request.json
    if not data:
        return jsonify({"msg": "参数不能为空"}), 400

    # print("新增客户账户信息：", data)
    try:
        item = CustomerAccount(
            customer_id=data["customer_id"],
            account_type=data["account_type"],
            account_no = data.get("account_no") or "",       # 防止 None
            bank_name = data.get("bank_name") or "" ,        # 防止 None
            remark = data.get("remark") or "",               # 防止 None
        )

        db.session.add(item)
        db.session.commit()

        return jsonify({"msg": "添加成功", "data": item.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "添加失败", "error": str(e)}), 500


# -------------------------------------------------
# 客户支付账户列表（支持 customer_id 筛选）
# -------------------------------------------------
@customer_account_bp.get("/list")
def list_accounts():
    customer_id = request.args.get("customer_id", type=int)

    query = CustomerAccount.query.filter_by(is_deleted=False)

    if customer_id:
        query = query.filter_by(customer_id=customer_id)

    items = query.order_by(CustomerAccount.id.desc()).all()

    return jsonify({
        "msg": "获取成功",
        "total": len(items),
        "data": [item.to_dict() for item in items]
    })


# -------------------------------------------------
# 获取单条账户信息
# -------------------------------------------------
@customer_account_bp.get("/detail/<int:id>")
def account_detail(id):
    item = CustomerAccount.query.get_or_404(id)
    return jsonify({"msg": "获取成功", "data": item.to_dict()})


# -------------------------------------------------
# 修改客户支付账户
# -------------------------------------------------
@customer_account_bp.put("/update/<int:id>")
def update_account(id):
    item = CustomerAccount.query.get_or_404(id)
    data = request.json

    try:
        item.account_type = data.get("account_type", item.account_type)
        item.account_no = data.get("account_no", item.account_no)
        item.bank_name = data.get("bank_name", item.bank_name)
        item.remark = data.get("remark", item.remark)

        db.session.commit()
        return jsonify({"msg": "修改成功", "data": item.to_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "修改失败", "error": str(e)}), 500


# -------------------------------------------------
# 软删除客户支付账户
# -------------------------------------------------
@customer_account_bp.delete("/delete/<int:id>")
def delete_account(id):
    item = CustomerAccount.query.get_or_404(id)

    try:
        item.is_deleted = True
        item.deleted_at = datetime.utcnow()

        db.session.commit()
        return jsonify({"msg": "删除成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "删除失败", "error": str(e)}), 500
