import psycopg

# Connect to the database we created
connection = psycopg.connect(
    dbname="studentCourses",
    user="postgres",
    password="postgres",
    host="localhost"
)

# Open a cursor to perform database operations
with connection.cursor() as cur:

    # Execute our Select all command
    cur.execute("""
                select * from students;
                """)
    
    #print outputs
    print(cur.fetchall())
    