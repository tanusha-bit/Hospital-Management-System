import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Crime@123",
        database="hospital"
    )
    cursor = conn.cursor()

    # Step 1: Change patient's contact_no to email
    try:
        cursor.execute("ALTER TABLE patient CHANGE contact_no email VARCHAR(255) NOT NULL")
        print("Successfully changed contact_no to email.")
    except mysql.connector.Error as err:
        print(f"Patient alter info: {err}")

    # Step 2: Add reason to appointment
    try:
        cursor.execute("ALTER TABLE appointment ADD COLUMN reason VARCHAR(255)")
        print("Successfully added reason to appointment.")
    except mysql.connector.Error as err:
        print(f"Appointment reason info: {err}")
        
    # Step 3: Ensure doc_id allows NULL
    try:
        # Since it was created as `doc_id INT`, it inherently allows NULL, but let's just make sure
        cursor.execute("ALTER TABLE appointment MODIFY doc_id INT NULL")
        print("Successfully verified doc_id allows NULL.")
    except mysql.connector.Error as err:
        print(f"Appointment doc_id info: {err}")

    conn.commit()
    cursor.close()
    conn.close()
    print("Database schema successfully updated!")

except mysql.connector.Error as err:
    print(f"Connection Error: {err}")
