#!/usr/bin/env python3
"""
Script to clear all data from the database tables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal, engine
from backend import models

def clear_database():
    """Clear all data from all tables"""
    
    print("🗑️  Clearing database...")
    
    # Create a session
    session = SessionLocal()
    
    try:
        # Delete all records from each table
        tables_cleared = 0
        
        # Clear transactions table
        transaction_count = session.query(models.Transaction).count()
        session.query(models.Transaction).delete()
        print(f"   ✅ Deleted {transaction_count} transactions")
        tables_cleared += 1
        
        # Clear events table (if exists)
        try:
            event_count = session.query(models.Event).count()
            session.query(models.Event).delete()
            print(f"   ✅ Deleted {event_count} events")
            tables_cleared += 1
        except Exception:
            print("   ℹ️  No events table found")
        
        # Commit the changes
        session.commit()
        
        print(f"\n🎉 Database cleared successfully!")
        print(f"   📊 Tables cleared: {tables_cleared}")
        print(f"   💾 Database file: bist.db")
        print(f"\n   Ready to import fresh data! 🚀")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error clearing database: {e}")
        return False
    finally:
        session.close()
    
    return True

def reset_database_schema():
    """Drop and recreate all tables"""
    print("\n🔄 Resetting database schema...")
    
    try:
        # Drop all tables
        models.Base.metadata.drop_all(bind=engine)
        print("   ✅ Dropped all tables")
        
        # Recreate all tables
        models.Base.metadata.create_all(bind=engine)
        print("   ✅ Recreated all tables")
        
        print("\n🎉 Database schema reset successfully!")
        
    except Exception as e:
        print(f"❌ Error resetting schema: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧹 Database Cleanup Tool")
    print("=" * 40)
    
    choice = input("\nChoose an option:\n1. Clear data only (keep schema)\n2. Full reset (drop & recreate tables)\n\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        success = clear_database()
    elif choice == "2":
        success = reset_database_schema()
    else:
        print("❌ Invalid choice. Please run again and select 1 or 2.")
        sys.exit(1)
    
    if success:
        print("\n✨ All done! You can now import your transactions fresh.")
    else:
        print("\n💥 Something went wrong. Please check the errors above.")
        sys.exit(1) 