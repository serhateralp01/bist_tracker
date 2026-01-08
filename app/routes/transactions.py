from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from app import db, models
from app.utils.data_import_export import export_transactions_to_csv, export_transactions_to_excel
from datetime import datetime

bp = Blueprint('transactions', __name__)

@bp.route('/transactions', methods=['GET'])
def list_transactions():
    transactions = db.session.query(models.Transaction).order_by(models.Transaction.date.desc()).all()
    return render_template('transactions.html', transactions=transactions)

@bp.route('/transactions/add', methods=['POST'])
def add_transaction():
    try:
        date_str = request.form.get('date')
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        tx = models.Transaction(
            type=request.form.get('type'),
            symbol=request.form.get('symbol'),
            quantity=float(request.form.get('quantity')),
            price=float(request.form.get('price')) if request.form.get('price') else None,
            date=date_obj,
            note=request.form.get('note')
        )
        db.session.add(tx)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding transaction: {str(e)}', 'danger')

    return redirect(url_for('transactions.list_transactions'))

@bp.route('/transactions/delete/<int:id>', methods=['POST'])
def delete_transaction(id):
    tx = db.session.query(models.Transaction).get(id)
    if tx:
        db.session.delete(tx)
        db.session.commit()
        flash('Transaction deleted.', 'success')
    else:
        flash('Transaction not found.', 'danger')
    return redirect(url_for('transactions.list_transactions'))

@bp.route('/transactions/export/csv')
def export_csv():
    try:
        csv_content = export_transactions_to_csv(db.session)
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=transactions.csv"}
        )
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'danger')
        return redirect(url_for('transactions.list_transactions'))
