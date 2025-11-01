#!/usr/bin/env python3
"""
Run database migration to add user_id column to investment_categories
"""
import os
import sys
import psycopg2

# Get database credentials from environment
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME', 'finance')
CLOUD_SQL_CONNECTION_NAME = os.getenv('CLOUD_SQL_CONNECTION_NAME')

if CLOUD_SQL_CONNECTION_NAME:
    # Cloud SQL connection
    connection_string = f"host=/cloudsql/{CLOUD_SQL_CONNECTION_NAME} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
else:
    print("Error: CLOUD_SQL_CONNECTION_NAME not set")
    sys.exit(1)

print(f"Connecting to database: {DB_NAME}")

try:
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()
    
    print("Adding user_id column to investment_categories...")
    cursor.execute("""
        ALTER TABLE investment_categories 
        ADD COLUMN IF NOT EXISTS user_id INTEGER;
    """)
    
    print("Adding foreign key constraint...")
    cursor.execute("""
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
    """)
    
    conn.commit()
    
    print("\nVerifying schema...")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'investment_categories'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    print("\nInvestment Categories Table Structure:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
    
    cursor.close()
    conn.close()
    
    print("\n✓ Migration completed successfully!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
