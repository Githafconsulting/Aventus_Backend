"""
Test different Supabase connection methods
"""
import psycopg2
from urllib.parse import quote_plus

password = "Aventus123"
project_ref = "mhrmbwsjjivckttokdiz"

# Try different connection strings
connection_strings = [
    # Direct connection
    f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres",

    # IPv4 mode
    f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres?sslmode=require",

    # Pooler - Transaction mode (port 6543)
    f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres",

    # Pooler - Session mode (port 5432)
    f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:5432/postgres",
]

regions = ["us-east-1", "us-west-1", "eu-west-1", "ap-southeast-1", "ap-northeast-1"]

print("Testing Supabase database connections...\n")

# Test direct connections first
for i, conn_str in enumerate(connection_strings, 1):
    print(f"Test {i}: Trying connection...")
    try:
        conn = psycopg2.connect(conn_str)
        conn.close()
        print(f"SUCCESS! Working connection string:")
        print(f"   {conn_str}")
        print("\nUse this in your .env file!")
        exit(0)
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        print(f"Failed: {error_msg}\n")

# Try different regions for pooler
print("Trying different regions...")
for region in regions:
    for port in [6543, 5432]:
        conn_str = f"postgresql://postgres.{project_ref}:{password}@aws-0-{region}.pooler.supabase.com:{port}/postgres"
        try:
            conn = psycopg2.connect(conn_str, connect_timeout=3)
            conn.close()
            print(f"\nSUCCESS! Working connection string:")
            print(f"   {conn_str}")
            print("\nUse this in your .env file!")
            exit(0)
        except:
            pass

print("\nCould not connect with any method.")
print("\nSolutions:")
print("1. Check if your Supabase project is paused")
print("2. Go to: https://supabase.com/dashboard/project/mhrmbwsjjivckttokdiz/settings/database")
print("3. Look for 'Connection string' and copy the exact URI")
print("4. Make sure database is not paused")
