import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT id, title, fetch_status, 
           LENGTH(description) as desc_len, 
           LENGTH(original_html) as html_len,
           fetch_error
    FROM articles 
    WHERE title LIKE '%Sponsor%WorkOS%'
    LIMIT 5
""")

rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]}")
    print(f"Title: {row[1]}")
    print(f"Fetch Status: {row[2]}")
    print(f"Description Length: {row[3]}")
    print(f"Original HTML Length: {row[4]}")
    print(f"Fetch Error: {row[5]}")
    print()

conn.close()
