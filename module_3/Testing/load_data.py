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

    # Execute our select all command
    cur.execute("""
            CREATE TABLE IF NOT EXISTS applicants (
                p_id SERIAL PRIMARY KEY,
                program TEXT,
                comments TEXT,
                date_added DATE,
                url TEXT,
                status TEXT,
                term TEXT,
                us_or_international TEXT,
                gpa FLOAT,
                gre FLOAT,
                gre_v FLOAT,
                gre_aw FLOAT,
                degree TEXT,
                llm_generated_program TEXT,
                llm_generated_university TEXT
                );
                """)
    cur.execute("""
            INSERT INTO applicants (
                program, comments, date_added, url, status, term, us_or_international, gpa, gre, gre_v, gre_aw,
                degree, llm_generated_program, llm_generated_university
                ) VALUES (
                'Computer Science MS',
                'Test entry',
                '2025-01-01',
                'http://example.com',
                'Accepted',
                'Fall 2025',
                'US',
                '3.8',
                '165',
                '160',
                '4.5',
                'Masters',
                'Computer Science',
                'Standford University'
                );
                """)
    connection.commit()
    connection.close()

    print("Applicants table created successfully.")

# re-Connect to the database we created
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
                select * from applicants;
                """)
    
    #print outputs
    print(cur.fetchall())
