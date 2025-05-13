Here are the simple instructions to add Young's Literal Translation (YLT) to your `bible_db`. This assumes you’re using a SQLite database and have Python installed. We'll use a script to download, parse, and integrate the YLT data.

---

### Simple Instructions to Add YLT to `bible_db`

1. **Download YLT Files**
   - Go to [eBible.org](https://ebible.org/Scriptures/engylt_usfm.zip) and download the YLT USFM ZIP file.
   - Extract it to a folder (e.g., `engylt_usfm`).

2. **Set Up Your `.env` File**
   - Add this line to your `.env` file (create one if it doesn’t exist):
     ```
     BIBLE_DB_PATH=/path/to/your/bible_db.sqlite
     ```
   - Replace `/path/to/your/bible_db.sqlite` with the path to your database.

3. **Install Required Libraries**
   - Run these commands in your terminal:
     ```bash
     pip install usfm python-dotenv
     ```

4. **Run the Integration Script**
   - Save and run the script below to add YLT to your `bible_db`. Update the `usfm_dir` path to match your extracted folder.

```python
import sqlite3
import usfm
import os
from dotenv import load_dotenv

load_dotenv()

def integrate_ylt(usfm_dir, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    usfm_files = usfm.load_directory(usfm_dir)
    
    for book in usfm_files:
        for chapter in usfm_files[book]:
            for verse in usfm_files[book][chapter]:
                text = usfm_files[book][chapter][verse]
                cursor.execute(
                    "INSERT INTO verses (book, chapter, verse, text, translation) VALUES (?, ?, ?, ?, 'YLT')",
                    (book, chapter, verse, text)
                )
    
    conn.commit()
    conn.close()
    print("YLT added to bible_db successfully.")

if __name__ == "__main__":
    usfm_dir = "path/to/engylt_usfm"  # Update this to your extracted folder
    db_path = os.getenv("BIBLE_DB_PATH")
    integrate_ylt(usfm_dir, db_path)
```

5. **Run the Script**
   - In your terminal, navigate to the script’s directory and run:
     ```bash
     python integrate_ylt.py
     ```

6. **Check the Results**
   - Open your database and run this SQL query to verify:
     ```sql
     SELECT * FROM verses WHERE translation = 'YLT' LIMIT 5;
     ```

---

That’s it! YLT should now be in your `bible_db`. If your `verses` table has a different structure, adjust the `INSERT` statement in the script accordingly. Let me know if you hit any snags!