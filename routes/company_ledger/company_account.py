from flask import Blueprint, request, jsonify
from db_config import db
from models import CompanyAccount, Company
from utils.decorators import login_required, roles_required

company_account_bp = Blueprint('company_account', __name__, url_prefix="/api/company_account")


# -------------------------------
# 工具：序列化
# -------------------------------
def model_to_dict(obj):
    """将 CompanyAccount 实例转换为 dict"""
    return {
        "id": obj.id,
        "company_id": obj.company_id,
        "company_name": obj.company.name if obj.company else None,
        "account_name": obj.account_name,
        "account_type": obj.account_type,
        "account_no": obj.account_no,
        "bank_name": obj.bank_name,
        "currency": obj.currency,
        "balance": float(obj.balance or 0),
        "status": obj.status,
        "remark": obj.remark,
        "created_at": obj.created_at.strftime("%Y-%m-%d %H:%M:%S") if obj.created_at else None,
        "updated_at": obj.updated_at.strftime("%Y-%m-%d %H:%M:%S") if obj.updated_at else None
    }


# -------------------------------
# 1. 新增公司账户
# -------------------------------
@company_account_bp.route("/add", methods=["POST"])
@login_required
def add_account():
    data = request.json
    print("新增公司账户信息：", data)

    try:
        account = CompanyAccount(
            company_id=data["company_id"],
            account_name=data["account_name"],
            account_type=data["account_type"],
            account_no=data.get("account_no"),
            bank_name=data.get("bank_name"),
            currency=data.get("currency", "CNY"),
            balance=data.get("balance", 0),
            status=data.get("status", "正常"),
            remark=data.get("remark")
        )
        db.session.add(account)
        db.session.commit()

        return jsonify({"success": True, "message": "新增成功", "data": model_to_dict(account)})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# -------------------------------
# 2. 编辑公司账户
# -------------------------------
@company_account_bp.route("/update/<int:account_id>", methods=["PUT"])
def update_account(account_id):
    data = request.json
    account = CompanyAccount.query.get_or_404(account_id)

    try:
        account.company_id = data.get("company_id", account.company_id)
        account.account_name = data.get("account_name", account.account_name)
        account.account_type = data.get("account_type", account.account_type)
        account.account_no = data.get("account_no", account.account_no)
        account.bank_name = data.get("bank_name", account.bank_name)
        account.currency = data.get("currency", account.currency)
        account.balance = data.get("balance", account.balance)
        account.status = data.get("status", account.status)
        account.remark = data.get("remark", account.remark)

        db.session.commit()

        return jsonify({"success": True, "message": "更新成功", "data": model_to_dict(account)})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# -------------------------------
# 3. 删除（软删除）公司账户
# -------------------------------
@company_account_bp.route("/delete/<int:account_id>", methods=["DELETE"])
def delete_account(account_id):
    account = CompanyAccount.query.get_or_404(account_id)

    try:
        db.session.delete(account)  # 因为公司账户不包含 is_deleted，这里直接删除
        db.session.commit()
        return jsonify({"success": True, "message": "删除成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# -------------------------------
# 4. 分页查询公司账户
# -------------------------------
@company_account_bp.route("/list", methods=["GET"])
def list_accounts():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    company_id = request.args.get("company_id")

    query = CompanyAccount.query

    if company_id:
        query = query.filter(CompanyAccount.company_id == company_id)

    pagination = query.order_by(CompanyAccount.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "success": True,
        "data": {
            "items": [model_to_dict(item) for item in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page
        }
    })


# -------------------------------
# 5. 查询所有公司账户（不分页）
# -------------------------------
@company_account_bp.route("/all", methods=["GET"])
def list_all_accounts():
    company_id = request.args.get("company_id")

    query = CompanyAccount.query

    if company_id:
        query = query.filter(CompanyAccount.company_id == company_id)

    items = query.order_by(CompanyAccount.id.desc()).all()

    return jsonify({
        "success": True,
        "items": [model_to_dict(item) for item in items],
        "total": len(items)
    })


# -------------------------------
# 5. 获取所有公司，用于前端下拉框
# -------------------------------
@company_account_bp.route("/companies", methods=["GET"])
def get_companies():
    companies = Company.query.all()
    return jsonify({
        "success": True,
        "data": [{"id": c.id, "name": c.name} for c in companies]
    })
