from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'))
conn = engine.connect()
result = conn.execute(text('SELECT id, name, template_type, country, is_active FROM templates'))

print('\nTemplates in database:')
print('=' * 100)
for row in result:
    print(f'Name: {row[1]}')
    print(f'Type: {row[2]}')
    print(f'Country: {row[3] if row[3] else "All Countries"}')
    print(f'Status: {"Active" if row[4] else "Inactive"}')
    print('-' * 100)

conn.close()
