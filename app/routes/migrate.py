"""
Migration route - TEMPORARY
Run database migrations via HTTP endpoint
"""
from flask import Blueprint, jsonify
from sqlalchemy import text
from app import db
import os

bp = Blueprint('migrate', __name__, url_prefix='/migrate')

# Security: Only allow if secret key matches
MIGRATION_SECRET = os.getenv('SECRET_KEY')

@bp.route('/add-investment-user-id/<secret>')
def add_investment_user_id(secret):
    """Add user_id column to investment_categories table"""
    
    if secret != MIGRATION_SECRET[:20]:  # Use first 20 chars as secret
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Add column
        db.session.execute(text("""
            ALTER TABLE investment_categories 
            ADD COLUMN IF NOT EXISTS user_id INTEGER;
        """))
        
        # Add constraint
        db.session.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'investment_categories_user_id_fkey'
                ) THEN
                    ALTER TABLE investment_categories 
                    ADD CONSTRAINT investment_categories_user_id_fkey 
                    FOREIGN KEY (user_id) REFERENCES users(id);
                END IF;
            END $$;
        """))
        
        db.session.commit()
        
        # Verify
        result = db.session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'investment_categories'
            ORDER BY ordinal_position;
        """))
        
        columns = [{'name': row[0], 'type': row[1], 'nullable': row[2]} for row in result]
        
        return jsonify({
            'status': 'success',
            'message': 'Migration completed successfully',
            'columns': columns
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
