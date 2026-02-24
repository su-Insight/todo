import sqlite3

conn = sqlite3.connect('backend/app.db')
cursor = conn.cursor()

# 查看 Task 表的内容
cursor.execute("SELECT id, date, text, tag, completed FROM tasks")
tasks = cursor.fetchall()

print("Tasks table:")
for task in tasks:
    print(task)

# 查看 history 表的内容
cursor.execute("SELECT * FROM history")
history = cursor.fetchall()

print("\nHistory table:")
for h in history:
    print(h)

conn.close()
