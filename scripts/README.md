# Utility Scripts

Helper scripts for database setup, initialization, and maintenance.

## Available Scripts

### `init_db.py`
Initialize the database with schema.

```bash
python scripts/init_db.py
```

Creates all tables defined in models.

### `init_user_categories.py`
Create default expense and income categories for a user.

```bash
python scripts/init_user_categories.py
```

Sets up common categories like:
- Groceries, Dining, Transportation
- Utilities, Insurance, Healthcare
- Salary, Bonus, Investment Income

### `update_db.py`
Run database migrations.

```bash
python scripts/update_db.py
```

Applies pending Alembic migrations.

### `auto_categorize.py`
Batch categorize transactions based on description patterns.

```bash
python scripts/auto_categorize.py
```

Uses regex patterns to automatically categorize uncategorized transactions.

### `fix_errors.py`
Fix data integrity issues.

```bash
python scripts/fix_errors.py
```

### `error_handler.py`
Error logging and handling utilities.

### `ai_error_fixer.py`
AI-powered error detection and fixing.

---

All scripts should be run from the project root directory.
