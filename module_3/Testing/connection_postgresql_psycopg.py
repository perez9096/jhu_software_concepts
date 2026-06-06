import psycopg

# Connect to the database we created
connection = psycopg.connect(
    dbname="studentCourses",
    user="psycopg",
)

# Open a cursor to perform database operations
with connection.cursor() as cur:
    # Execute our Select all command
    cur.execute(
        """
        SELECT * FROM students;
        """
    )
    # Print outputs
    print(cur.fetchall())


