from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, current_app, session
from flask_login import current_user, login_required
from app.services.receipt_ocr import ReceiptOCRAgent
from app.services.categorizer import TransactionCategorizer
from app.models import Receipt, Transaction, Account, Category
from app import db
from werkzeug.utils import secure_filename
from app.routes.settings import get_currency_info, get_current_currency
import json
from datetime import datetime

bp = Blueprint('receipts', __name__, url_prefix='/receipts')

@bp.route('/')
@login_required
def index():
    """Receipt management dashboard"""
    agent = ReceiptOCRAgent()
    stats = agent.get_receipt_stats(current_user.id)

    # Get recent receipts for current user only
    recent_receipts = Receipt.query.join(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Receipt.uploaded_at.desc()).limit(20).all()

    return render_template('receipts/index.html',
                         stats=stats,
                         receipts=recent_receipts)

@bp.route('/upload/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def upload(transaction_id):
    """Upload receipt for a transaction"""
    transaction = Transaction.query.get_or_404(transaction_id)

    # Verify user owns this transaction
    if transaction.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('receipts.index'))

    if request.method == 'POST':
        if 'receipt_file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)

        file = request.files['receipt_file']

        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)

        agent = ReceiptOCRAgent()

        if not agent.allowed_file(file.filename):
            flash('Invalid file type. Allowed types: PNG, JPG, JPEG, PDF, WEBP', 'danger')
            return redirect(request.url)

        # Process receipt
        receipt, parsed_data = agent.process_receipt(current_user.id, file, transaction_id)

        if not receipt:
            flash(f'Error processing receipt: {parsed_data}', 'danger')
            return redirect(request.url)

        # Optionally update transaction with extracted data
        if request.form.get('auto_update') == 'on':
            if parsed_data.get('date') and not transaction.date:
                transaction.date = parsed_data['date']
            if parsed_data.get('amount') and transaction.amount == 0:
                transaction.amount = parsed_data['amount']
            if parsed_data.get('merchant') and transaction.payee == 'Unknown':
                transaction.payee = parsed_data['merchant']

            db.session.commit()

        flash(f'Receipt uploaded and processed successfully! Found: {len(parsed_data.get("items", []))} items', 'success')
        return redirect(url_for('transactions.list_transactions'))

    return render_template('receipts/upload.html', transaction=transaction)

@bp.route('/review-statement', methods=['POST'])
def review_statement():
    """Review extracted statement transactions before importing"""
    # Get the parsed statement data from session or form
    import_data = request.get_json()

    if not import_data or 'transactions' not in import_data:
        return jsonify({'error': 'No transaction data provided'}), 400

    account_id = import_data.get('account_id')
    transactions = import_data.get('transactions', [])

    # Store in session for bulk import
    session['pending_import'] = {
        'account_id': account_id,
        'transactions': transactions
    }

    return jsonify({'success': True, 'count': len(transactions)})

@bp.route('/bulk-import', methods=['POST'])
@login_required
def bulk_import():
    """Import multiple transactions from reviewed statement data"""
    try:
        # Try to get data from JSON request body
        import_data = request.get_json()
        current_app.logger.debug(f"Bulk import request received. Import data present: {import_data is not None}")

        if import_data:
            # Data from AJAX request
            account_id = import_data.get('account_id')
            transactions_data = import_data.get('transactions', [])
            current_app.logger.info(f"Processing bulk import with {len(transactions_data)} transactions for account {account_id}")
        else:
            # Fallback to session data
            pending_data = session.get('pending_import')
            if not pending_data:
                current_app.logger.warning('No pending import data in session')
                return jsonify({'error': 'No pending import data found'}), 400

            account_id = pending_data['account_id']
            transactions_data = pending_data['transactions']
            current_app.logger.info(f"Processing bulk import from session with {len(transactions_data)} transactions for account {account_id}")

        if not account_id:
            current_app.logger.error('Account ID is missing or empty')
            return jsonify({'error': 'Account ID required'}), 400

        try:
            account = Account.query.get_or_404(account_id)
            current_app.logger.info(f"Found account: {account.name} (ID: {account_id})")
        except Exception as e:
            current_app.logger.error(f"Error finding account {account_id}: {str(e)}", exc_info=True)
            return jsonify({'error': f'Account not found: {account_id}'}), 404

        # Verify user owns this account
        if account.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403

        imported_count = 0
        for trans_data in transactions_data:
            # Validate required fields
            if not trans_data.get('date') or not trans_data.get('amount') or not trans_data.get('description'):
                continue  # Skip incomplete records

            try:
                # Parse date string if needed
                trans_date = trans_data['date']
                if isinstance(trans_date, str):
                    trans_date = datetime.strptime(trans_date, '%Y-%m-%d').date()

                # Parse amount
                amount = float(trans_data['amount'])

                # Parse category_id
                category_id = trans_data.get('category_id')
                if category_id:
                    try:
                        category_id = int(category_id)
                    except (ValueError, TypeError):
                        category_id = None

                # Amount already has correct sign from parse_statement_data:
                # Negative = charges/expenses (withdrawal), Positive = payments/credits (deposit)
                if amount >= 0:
                    # Positive amount = payment/credit
                    trans_type = 'deposit'
                else:
                    # Negative amount = charge/expense
                    trans_type = 'withdrawal'

                # Store amount as absolute value; transaction_type determines the sign
                abs_amount = abs(amount)

                # Create transaction
                transaction = Transaction(
                    user_id=current_user.id,
                    account_id=account_id,
                    date=trans_date,
                    payee=trans_data.get('description', 'Unknown'),
                    amount=abs_amount,
                    category_id=category_id,
                    transaction_type=trans_type
                )

                db.session.add(transaction)
                imported_count += 1
            except Exception as e:
                # Log error but continue with other transactions
                current_app.logger.warning(f"Error importing transaction from {trans_data.get('description', 'Unknown')}: {str(e)}")
                continue

        # Update account balance
        try:
            current_app.logger.info(f"Imported {imported_count} transactions, updating account balance...")
            db.session.flush()  # Flush to database so update_balance can see the new transactions
            account.update_balance()
            current_app.logger.info(f"Account balance updated. New balance: {account.current_balance}")
        except Exception as e:
            current_app.logger.error(f"Error updating account balance: {str(e)}", exc_info=True)
            db.session.rollback()
            raise

        try:
            db.session.commit()
            current_app.logger.info(f"Successfully committed {imported_count} transactions")
        except Exception as e:
            current_app.logger.error(f"Error committing transactions: {str(e)}", exc_info=True)
            db.session.rollback()
            raise

        # Create receipt record if we have pending receipt data (from session or request)
        receipt_data = None
        if 'pending_receipt' in session:
            receipt_data = session.get('pending_receipt')
        elif import_data and 'receipt_metadata' in import_data:
            receipt_data = import_data.get('receipt_metadata')

        if imported_count > 0 and receipt_data:
            try:
                agent = ReceiptOCRAgent()

                current_app.logger.info(f"Creating receipt record for {imported_count} imported transactions")
                current_app.logger.debug(f"Receipt data: {receipt_data}")

                # Get the first imported transaction to link to
                # (In bulk import, all transactions come from the same receipt)
                first_transaction = Transaction.query.filter_by(
                    account_id=account_id,
                    user_id=current_user.id
                ).order_by(Transaction.id.desc()).first()

                if first_transaction:
                    # Create receipt record linking to the first transaction
                    receipt = agent.create_receipt_record(
                        user_id=current_user.id,
                        filepath=receipt_data.get('filepath'),
                        filename=receipt_data.get('filename'),
                        transaction_id=first_transaction.id,
                        parsed_data={
                            'merchant': receipt_data.get('merchant', 'Bank Statement'),
                            'date': first_transaction.date,
                            'items': [
                                {
                                    'description': t.get('description', 'Unknown'),
                                    'amount': t.get('amount', 0.0),
                                    'date': t.get('date', '')
                                }
                                for t in transactions_data if t.get('description')
                            ]
                        },
                        file_type=receipt_data.get('file_type')
                    )

                    current_app.logger.info(f"✓ Created receipt record ID {receipt.id} for transaction ID {first_transaction.id}")

                    # Clear session data if it exists
                    session.pop('pending_receipt', None)
                else:
                    current_app.logger.warning(f"No transaction found to link receipt to for account {account_id}")
            except Exception as e:
                current_app.logger.error(f"Failed to create receipt record for bulk import: {str(e)}", exc_info=True)

        # Save category mappings for future use
        if imported_count > 0:
            categorizer = TransactionCategorizer(current_user.id)
            for trans_data in transactions_data:
                if trans_data.get('category_id') and trans_data.get('description'):
                    try:
                        categorizer.update_mapping(
                            payee=trans_data['description'],
                            category_id=int(trans_data['category_id'])
                        )
                    except Exception as e:
                        current_app.logger.warning(f"Failed to save category mapping: {str(e)}")

        # Clear session data if it exists
        if 'pending_import' in session:
            session.pop('pending_import', None)

        if import_data:
            # Return JSON for AJAX request
            return jsonify({'success': True, 'imported_count': imported_count})
        else:
            # Redirect for form request
            flash(f'Successfully imported {imported_count} transactions!', 'success')
            return redirect(url_for('transactions.list_transactions'))

    except Exception as e:
        # Return error response
        current_app.logger.error(f'Bulk import error: {str(e)}', exc_info=True)
        error_msg = f'Error importing transactions: {str(e)}'
        # Always return JSON since this is an AJAX endpoint
        return jsonify({'error': error_msg, 'success': False}), 400

@bp.route('/upload-new', methods=['GET', 'POST'])
@login_required
def upload_new():
    current_app.logger.info("--- In upload_new function ---")
    """Upload receipt and create new transaction"""
    if request.method == 'POST':
        if 'receipt_file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)

        file = request.files['receipt_file']
        account_id = request.form.get('account_id')
        pdf_password = request.form.get('pdf_password')

        if not account_id:
            flash('Please select an account', 'danger')
            return redirect(request.url)

        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)

        agent = ReceiptOCRAgent()

        # Extract data without creating database records yet
        filepath, filename, parsed_data, file_type = agent.extract_receipt_data(file, current_user.id, 'temp', password=pdf_password)

        if not filepath:
            # Check if PDF password is required
            if parsed_data == 'PDF_PASSWORD_REQUIRED':
                return jsonify({'error': 'PDF_PASSWORD_REQUIRED'}), 200

            # Check for password errors
            if 'password' in str(parsed_data).lower():
                return jsonify({'error': parsed_data}), 200

            flash(f'Error processing receipt: {parsed_data}', 'danger')
            return redirect(request.url)

        # Store file info in session for later receipt creation
        session['pending_receipt'] = {
            'filepath': filepath,
            'filename': filename,
            'file_type': file_type
        }

        # Extract statement info and determine extraction method
        statement_info = None
        line_items = parsed_data.get('line_items', [])
        extraction_method = parsed_data.get('_extraction_method', 'ocr')

        # Debug logging
        current_app.logger.info(f"Extracted {len(line_items)} line items from receipt using {extraction_method}")
        current_app.logger.debug(f"Parsed data: {parsed_data}")

        # Check if extraction was successful
        if not line_items or len(line_items) == 0:
            error_msg = "Unable to extract any transactions from the uploaded image. We tried:\n• Step 1: AI analysis\n• Step 2: OCR text extraction\n\nPlease ensure the image is clear and contains visible transaction data with dates, descriptions, and amounts."
            current_app.logger.warning(f"Empty extraction result for file: {filename}")
            return jsonify({
                'error': error_msg,
                'extraction_method': extraction_method,
                'steps_tried': ['ai', 'ocr']
            }), 400

        # If we have multi-line transactions, use them
        if line_items and len(line_items) > 0:
            if '_statement_info' in line_items[0]:
                statement_info = line_items[0]['_statement_info']

        # Always return as line_items for consistent handling
        return jsonify({
            'line_items': [
                {
                    'date': item['date'].isoformat() if hasattr(item.get('date'), 'isoformat') else str(item.get('date', '')),
                    'description': item.get('description', 'Unknown'),
                    'amount': item.get('amount', 0.0),
                    '_statement_info': item.get('_statement_info'),
                    'category': item.get('category')
                }
                for item in line_items
            ],
            'statement_info': statement_info,
            'extraction_method': extraction_method,
            'transaction_count': len(line_items)
        })

    accounts = Account.query.filter_by(user_id=current_user.id, is_active=True).all()
    currency_info = get_currency_info()
    return render_template('receipts/upload_new.html',
                         accounts=accounts,
                         currency_symbol=currency_info['symbol'],
                         currency_code=get_current_currency())

@bp.route('/confirm-receipt', methods=['POST'])
@login_required
def confirm_receipt():
    """Confirm and create transaction from reviewed receipt data"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    account_id = data.get('account_id')
    transaction_date = data.get('date')
    merchant = data.get('description') or data.get('merchant')
    amount = data.get('amount')
    category_id = data.get('category_id')

    if not account_id or not transaction_date or not merchant or amount is None:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Verify user owns the account
        account = Account.query.get_or_404(account_id)
        if account.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403

        # Create transaction with reviewed data
        transaction = Transaction(
            user_id=current_user.id,
            date=datetime.strptime(transaction_date, '%Y-%m-%d').date() if isinstance(transaction_date, str) else transaction_date,
            amount=float(amount),
            payee=merchant,
            transaction_type='withdrawal',
            account_id=int(account_id),
            category_id=int(category_id) if category_id else None
        )

        db.session.add(transaction)
        db.session.commit()

        # Create receipt record if we have pending receipt data
        if 'pending_receipt' in session:
            agent = ReceiptOCRAgent()
            receipt_data = session['pending_receipt']

            # Create receipt record linking to the new transaction
            agent.create_receipt_record(
                user_id=current_user.id,
                filepath=receipt_data['filepath'],
                filename=receipt_data['filename'],
                transaction_id=transaction.id,
                parsed_data={'merchant': merchant, 'date': transaction.date, 'amount': amount},
                file_type=receipt_data['file_type']
            )

            # Clear session data
            session.pop('pending_receipt', None)

        # Update account balance
        account.update_balance()
        db.session.commit()

        return jsonify({
            'success': True,
            'transaction_id': transaction.id,
            'redirect_url': url_for('transactions.edit_transaction', id=transaction.id)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/camera/<int:transaction_id>')
@login_required
def camera_capture(transaction_id):
    """Camera capture page for receipt"""
    transaction = Transaction.query.get_or_404(transaction_id)

    # Verify user owns this transaction
    if transaction.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('receipts.index'))

    return render_template('receipts/camera.html', transaction=transaction)

@bp.route('/view/<int:receipt_id>')
@login_required
def view(receipt_id):
    """View receipt details"""
    receipt = Receipt.query.get_or_404(receipt_id)

    # Verify user owns this receipt
    if receipt.transaction.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('receipts.index'))

    # Parse items if available
    items = []
    if receipt.extracted_items:
        try:
            items = json.loads(receipt.extracted_items)
        except:
            pass

    return render_template('receipts/view.html', receipt=receipt, items=items)

@bp.route('/image/<int:receipt_id>')
@login_required
def serve_image(receipt_id):
    """Serve receipt image"""
    receipt = Receipt.query.get_or_404(receipt_id)

    # Verify user owns this receipt
    if receipt.transaction.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('receipts.index'))

    import os
    if os.path.exists(receipt.filepath):
        return send_file(receipt.filepath)
    else:
        flash('Receipt image not found', 'danger')
        return redirect(url_for('receipts.index'))

@bp.route('/delete/<int:receipt_id>', methods=['POST'])
@login_required
def delete(receipt_id):
    """Delete receipt"""
    receipt = Receipt.query.get_or_404(receipt_id)

    # Verify user owns this receipt
    if receipt.transaction.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('receipts.index'))

    agent = ReceiptOCRAgent()
    success, message = agent.delete_receipt(receipt_id)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(request.referrer or url_for('receipts.index'))

@bp.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    """API endpoint to get available categories for current user"""
    categories = Category.query.filter_by(user_id=current_user.id, is_income=False).all()
    return jsonify({
        'categories': [
            {'id': cat.id, 'name': cat.name}
            for cat in categories
        ]
    })

@bp.route('/api/suggest-categories', methods=['POST'])
@login_required
def suggest_categories():
    """API endpoint to suggest categories for merchants using smart categorization"""
    data = request.get_json()

    if not data or 'merchants' not in data:
        return jsonify({'error': 'No merchants provided'}), 400

    merchants = data.get('merchants', [])
    if not isinstance(merchants, list) or len(merchants) == 0:
        return jsonify({'error': 'merchants must be a non-empty array'}), 400

    try:
        categorizer = TransactionCategorizer(current_user.id)
        suggestions = []

        for merchant in merchants:
            if not merchant or not merchant.strip():
                suggestions.append({
                    'merchant': merchant,
                    'category_id': None,
                    'category_name': None
                })
                continue

            # Get category suggestion
            category_id, is_from_cache, reason = categorizer.categorize_transaction(
                payee=merchant.strip(),
                description=None,
                amount=None
            )

            if category_id:
                # Get category name
                category = Category.query.get(category_id)
                suggestions.append({
                    'merchant': merchant,
                    'category_id': category_id,
                    'category_name': category.name if category else None,
                    'is_cached': is_from_cache
                })
            else:
                suggestions.append({
                    'merchant': merchant,
                    'category_id': None,
                    'category_name': None
                })

        return jsonify({
            'success': True,
            'suggestions': suggestions
        })

    except Exception as e:
        current_app.logger.error(f"Error suggesting categories: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    """API endpoint for camera/mobile upload"""
    if 'receipt_image' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['receipt_image']
    transaction_id = request.form.get('transaction_id')

    if not transaction_id:
        return jsonify({'error': 'Transaction ID required'}), 400

    # Verify user owns this transaction
    transaction = Transaction.query.get(int(transaction_id))
    if not transaction or transaction.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    agent = ReceiptOCRAgent()
    receipt, parsed_data = agent.process_receipt(file, int(transaction_id))

    if not receipt:
        return jsonify({'error': parsed_data}), 400

    return jsonify({
        'success': True,
        'receipt_id': receipt.id,
        'extracted_data': {
            'merchant': parsed_data.get('merchant'),
            'date': str(parsed_data.get('date')) if parsed_data.get('date') else None,
            'amount': parsed_data.get('amount'),
            'items_count': len(parsed_data.get('items', []))
        }
    })

@bp.route('/match/<int:receipt_id>')
@login_required
def auto_match(receipt_id):
    """Try to auto-match receipt to existing transaction"""
    receipt = Receipt.query.get_or_404(receipt_id)

    # Verify user owns this receipt
    if receipt.transaction.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('receipts.index'))

    agent = ReceiptOCRAgent()

    # Get parsed data
    parsed_data = {
        'date': receipt.extracted_date,
        'amount': receipt.extracted_amount,
        'merchant': receipt.extracted_merchant
    }

    # Try to find matching transaction
    matched_transaction = agent.auto_match_receipt(parsed_data)

    if matched_transaction:
        # Link receipt to matched transaction
        receipt.transaction_id = matched_transaction.id
        db.session.commit()

        flash(f'Receipt automatically matched to transaction: {matched_transaction.payee}', 'success')
        return redirect(url_for('transactions.list_transactions'))
    else:
        flash('Could not find matching transaction. Please match manually.', 'warning')
        return redirect(url_for('receipts.view', receipt_id=receipt_id))

from datetime import datetime
