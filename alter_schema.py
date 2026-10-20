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

    # Step 4: Ensure support tables for new pharmacist and nurse sections exist
    table_statements = [
        ("""
            CREATE TABLE IF NOT EXISTS nurse (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                specialization VARCHAR(255) NOT NULL,
                contact_no VARCHAR(20) NOT NULL
            )
        """, "nurse"),
        ("""
            CREATE TABLE IF NOT EXISTS pharmacist (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                contact_no VARCHAR(20) NOT NULL
            )
        """, "pharmacist"),
        ("""
            CREATE TABLE IF NOT EXISTS prescription (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT NOT NULL,
                doctor_id INT NOT NULL,
                medicine_name VARCHAR(255) NOT NULL,
                dosage VARCHAR(255) NOT NULL,
                instructions TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patient(id) ON DELETE CASCADE,
                FOREIGN KEY (doctor_id) REFERENCES doctor(id) ON DELETE CASCADE
            )
        """, "prescription"),
        ("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                medicine_name VARCHAR(255) NOT NULL,
                category VARCHAR(255) NOT NULL,
                stock_quantity INT NOT NULL,
                unit_price VARCHAR(100) NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """, "inventory"),
        ("""
            CREATE TABLE IF NOT EXISTS patient_care (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT NOT NULL,
                nurse_id INT NOT NULL,
                care_note TEXT NOT NULL,
                status VARCHAR(100) DEFAULT 'In Progress',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patient(id) ON DELETE CASCADE,
                FOREIGN KEY (nurse_id) REFERENCES nurse(id) ON DELETE CASCADE
            )
        """, "patient_care")
    ]

    for query, table_name in table_statements:
        try:
            cursor.execute(query)
            print(f"Successfully ensured {table_name} table exists.")
        except mysql.connector.Error as err:
            print(f"{table_name} table info: {err}")

    conn.commit()
    cursor.close()
    conn.close()
    print("Database schema successfully updated!")

except mysql.connector.Error as err:
    print(f"Connection Error: {err}")
