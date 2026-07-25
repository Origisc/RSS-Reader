import sqlite3
import requests

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT id, title, link 
    FROM articles 
    WHERE title LIKE '%Sponsor%WorkOS%'
    LIMIT 5
""")

rows = cursor.fetchall()
for row in rows:
    article_id = row[0]
    title = row[1]
    link = row[2]
    
    print(f"ID: {article_id}")
    print(f"Title: {title}")
    print(f"Link: {link}")
    
    if link:
        try:
            print("\n--- Fetching original page ---")
            response = requests.get(link, timeout=10)
            response.encoding = response.apparent_encoding
            print(f"Status Code: {response.status_code}")
            print(f"Page Content Length: {len(response.text)}")
            print(f"\\nPage Preview (first 1000 chars):")
            print(response.text[:1000])
        except Exception as e:
            print(f"Fetch failed: {e}")
    print()

conn.close()
