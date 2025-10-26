"""Update database with new tables for agents"""
from app import create_app, db
from app.models import Receipt, TaxTag, CategorizationRule, FinancialInsight, Scenario

def update_database():
    app = create_app()

    with app.app_context():
        # Create all new tables
        print("Creating new agent tables...")
        db.create_all()
        print("Database updated successfully!")
        print("New tables: receipts, tax_tags, categorization_rules, financial_insights, scenarios")

if __name__ == '__main__':
    update_database()
