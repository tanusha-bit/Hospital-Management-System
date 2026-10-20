import mysql.connector

try:
    # Connect to MySQL Server bypassing the specific database
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Crime@123"
    )
    cursor = conn.cursor()

    # Create Database
    cursor.execute("CREATE DATABASE IF NOT EXISTS hospital")
    print("Database 'hospital' created successfully or already exists.")

    # Select the Database
    cursor.execute("USE hospital")

    # Create Patient Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patient (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        dob VARCHAR(50) NOT NULL,
        contact_no VARCHAR(20) NOT NULL
    )
    """)
    print("Table 'patient' created successfully.")

    # Create Doctor Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctor (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        specialization VARCHAR(255) NOT NULL,
        contact_no VARCHAR(20) NOT NULL
    )
    """)
    print("Table 'doctor' created successfully.")

    # Create Nurse Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nurse (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        specialization VARCHAR(255) NOT NULL,
        contact_no VARCHAR(20) NOT NULL
    )
    """)
    print("Table 'nurse' created successfully.")

    # Create Pharmacist Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pharmacist (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        contact_no VARCHAR(20) NOT NULL
    )
    """)
    print("Table 'pharmacist' created successfully.")

    # Create Appointment Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointment (
        id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT,
        doc_id INT,
        appointment_time VARCHAR(100) NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patient(id) ON DELETE CASCADE,
        FOREIGN KEY (doc_id) REFERENCES doctor(id) ON DELETE CASCADE
    )
    """)
    print("Table 'appointment' created successfully.")

    # Create Bills Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bills (
        id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT,
        treatment_name VARCHAR(255) NOT NULL,
        room_charges VARCHAR(100) NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patient(id) ON DELETE CASCADE
    )
    """)
    print("Table 'bills' created successfully.")

    # Create Prescription Table
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
    print("Table 'prescription' created successfully.")

    # Create Inventory Table
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
    print("Table 'inventory' created successfully.")

    # Create Patient Care Table
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
    print("Table 'patient_care' created successfully.")

    conn.commit()
    cursor.close()
    conn.close()
    print("All tables initialized successfully!")

except mysql.connector.Error as err:
    print(f"Error: {err}")
