from sqlalchemy import text
from backend.database import engine, SessionLocal

def migrate():
    with engine.connect() as connection:
        # Check if asset_type column exists
        try:
            connection.execute(text("SELECT asset_type FROM transactions LIMIT 1"))
            print("Column 'asset_type' already exists.")
        except Exception:
            print("Adding 'asset_type' column...")
            connection.execute(text("ALTER TABLE transactions ADD COLUMN asset_type VARCHAR DEFAULT 'STOCK'"))

        # Check if currency column exists
        try:
            connection.execute(text("SELECT currency FROM transactions LIMIT 1"))
            print("Column 'currency' already exists.")
        except Exception:
            print("Adding 'currency' column...")
            connection.execute(text("ALTER TABLE transactions ADD COLUMN currency VARCHAR DEFAULT 'TRY'"))

        connection.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
