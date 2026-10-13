import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Crime@123",
        database="hospital"
    )
    cursor = conn.cursor()

    # Step 1: Alter appointment table
    try:
        cursor.execute("ALTER TABLE appointment ADD COLUMN status VARCHAR(50) DEFAULT 'Pending'")
        print("Successfully added 'status' column to appointment.")
    except mysql.connector.Error as err:
        print(f"Appointment alter info: {err}")

    # Step 2: Alter bills table
    try:
        cursor.execute("ALTER TABLE bills CHANGE charges room_charges VARCHAR(100) NOT NULL")
        print("Successfully renamed 'charges' to 'room_charges' in bills.")
    except mysql.connector.Error as err:
        print(f"Bills alter info: {err}")

    conn.commit()
    cursor.close()
    conn.close()
    print("Database schema successfully updated!")

except mysql.connector.Error as err:
    print(f"Connection Error: {err}")
