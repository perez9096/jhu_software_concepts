import psycopg
from psycopg import OperationalError

# Connect to the database we created
connection = psycopg.connect(
    dbname="studentCourses",
    user="psycopg",
    password="your_password"  # Add your password here
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


