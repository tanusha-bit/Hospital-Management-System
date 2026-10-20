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

    # Step 3: Add nurse table when supported
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nurse (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                specialization VARCHAR(255) NOT NULL,
                contact_no VARCHAR(20) NOT NULL
            )
        """)
        print("Successfully ensured nurse table exists.")
    except mysql.connector.Error as err:
        print(f"Nurse table info: {err}")

    # Step 4: Add pharmacist table when supported
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pharmacist (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                contact_no VARCHAR(20) NOT NULL
            )
        """)
        print("Successfully ensured pharmacist table exists.")
    except mysql.connector.Error as err:
        print(f"Pharmacist table info: {err}")

    # Step 5: Add prescription table when supported
    try:
        cursor.execute("""
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
        """)
        print("Successfully ensured prescription table exists.")
    except mysql.connector.Error as err:
        print(f"Prescription table info: {err}")

    # Step 6: Add inventory table when supported
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                medicine_name VARCHAR(255) NOT NULL,
                category VARCHAR(255) NOT NULL,
                stock_quantity INT NOT NULL,
                unit_price VARCHAR(100) NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        print("Successfully ensured inventory table exists.")
    except mysql.connector.Error as err:
        print(f"Inventory table info: {err}")

    # Step 7: Add patient care table when supported
    try:
        cursor.execute("""
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
        """)
        print("Successfully ensured patient care table exists.")
    except mysql.connector.Error as err:
        print(f"Patient care table info: {err}")

    conn.commit()
    cursor.close()
    conn.close()
    print("Database schema successfully updated!")

except mysql.connector.Error as err:
    print(f"Connection Error: {err}")
