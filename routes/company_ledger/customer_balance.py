from flask import Blueprint, request, jsonify
from db_config import db
from models import CustomerBalance, Customer, Company
from decimal import Decimal

customer_balance_bp = Blueprint("customer_balance", __name__)


# -------------------------------
# 工具函数：模型转换为 dict
# -------------------------------
def balance_to_dict(balance: CustomerBalance):
    return {
        "id": balance.id,
        "customer_id": balance.customer_id,
        "customer_name": balance.customer.name if balance.customer else None,
        "company_id": balance.company_id,
        "company_name": balance.company.name if balance.company else None,
        "balance": float(balance.balance),
        "adjustment_total": float(balance.adjustment_total),
        "remark": balance.remark,
        "updated_at": balance.updated_at.strftime("%Y-%m-%d %H:%M:%S") if balance.updated_at else None,
    }


# -------------------------------
# 获取所有公司 + 客户（下拉框）
# -------------------------------
@customer_balance_bp.route("/options", methods=["GET"])
def get_options():
    companies = Company.query.all()
    customers = Customer.query.all()

    return jsonify({
        "success": True,
        "data": {
            "companies": [{"id": c.id, "name": c.name} for c in companies],
            "customers": [{"id": c.id, "name": c.name} for c in customers]
        }
    }), 200


# -------------------------------
# 获取余额列表（分页）
# 过滤：customer_id / company_id
# -------------------------------
@customer_balance_bp.route("/list", methods=["GET"])
def list_balances():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    customer_id = request.args.get("customer_id")
    company_id = request.args.get("company_id")

    query = CustomerBalance.query

    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if company_id:
        query = query.filter_by(company_id=company_id)

    pagination = query.order_by(CustomerBalance.updated_at.desc()).paginate(page=page, per_page=per_page)
    items = pagination.items

    return jsonify({
        "success": True,
        "data": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "items": [balance_to_dict(i) for i in items]
        }
    }), 200


# -------------------------------
# 新增客户余额
# -------------------------------
@customer_balance_bp.route("/add", methods=["POST"])
def add_balance():
    data = request.json
    print("客户余额项数据：", data)

    customer_id = data.get("customer_id")
    company_id = data.get("company_id")
    balance = Decimal(str(data.get("balance", 0)))
    adjustment_total = Decimal(str(data.get("adjustment_total", 0)))   # ← 加这行
    remark = data.get("remark")

    if not customer_id or not company_id:
        return jsonify({"success": False, "message": "customer_id 和 company_id 必填"}), 400

    # 唯一检查
    exists = CustomerBalance.query.filter_by(
        customer_id=customer_id,
        company_id=company_id
    ).first()

    if exists:
        return jsonify({"success": False, "message": "该客户在该公司下已存在余额记录"}), 400

    new_item = CustomerBalance(
        customer_id=customer_id,
        company_id=company_id,
        balance=balance,
        adjustment_total=adjustment_total,   # ← 加这行
        remark=remark
    )

    db.session.add(new_item)
    db.session.commit()

    return jsonify({"success": True, "message": "新增成功"}), 200



# -------------------------------
# 更新客户余额（含修改余额）
# -------------------------------
@customer_balance_bp.route("/update/<int:id>", methods=["PUT"])
def update_balance(id):
    data = request.json
    print('客户余额：',data)
    item = CustomerBalance.query.get(id)

    if not item:
        return jsonify({"success": False, "message": "记录不存在"}), 404

    item.remark = data.get("remark", item.remark)

    if "balance" in data:
        new_balance = Decimal(str(data["balance"])).quantize(Decimal("0.01"))

        old_balance = item.balance or Decimal("0.00")
        diff = new_balance - old_balance

        item.balance = new_balance

        print( 'old:',old_balance,'new',new_balance,'diff:',diff,'存入的累计：',item.adjustment_total)
        if item.adjustment_total is None:
            item.adjustment_total = Decimal("0.00")
        print( 'old:',old_balance,'new',new_balance,'diff:',diff,'存入的累计：',item.adjustment_total)
        item.adjustment_total = (item.adjustment_total + diff).quantize(Decimal("0.01"))
        print( 'old:',old_balance,'new',new_balance,'diff:',diff,'存入的累计：',item.adjustment_total)

    db.session.commit()

    return jsonify({"success": True, "message": "更新成功"}), 200


# -------------------------------
# 删除客户余额
# -------------------------------
@customer_balance_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_balance(id):
    item = CustomerBalance.query.get(id)

    if not item:
        return jsonify({"success": False, "message": "记录不存在"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"success": True, "message": "删除成功"}), 200
