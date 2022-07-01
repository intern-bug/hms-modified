import psycopg2


conn = psycopg2.connect(
    host="localhost",
    database="hosteldb",
    user="hosteladmin",
    password="hostel123"
)

cursor = conn.cursor()

cursor.execute('''select regd_no from institute_student''')

result = cursor.fetchall()

for row in result:
    cursor.execute('''
        update institute_student
        set photo = '{file}' where regd_no='{regd_no}'
    '''.format(file='Student-Photos/Year-2/placeholder.jpg', regd_no=row[0]))


conn.commit()

conn.close()