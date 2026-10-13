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
        charges VARCHAR(100) NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patient(id) ON DELETE CASCADE
    )
    """)
    print("Table 'bills' created successfully.")

    conn.commit()
    cursor.close()
    conn.close()
    print("All tables initialized successfully!")

except mysql.connector.Error as err:
    print(f"Error: {err}")
