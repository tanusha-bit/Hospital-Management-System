from flask import Flask, render_template, request, redirect
import mysql.connector
# Version 1: Demonstrating Git version control for HMS
app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Crime@123",
    database="hospital"
)

cursor = db.cursor()

@app.route('/')
def index():
    return render_template('index.html')

# ---------------- OPERATOR ----------------
@app.route('/operator')
def operator():
    return render_template('operator.html')

# ---------------- PATIENT ----------------
@app.route('/patient')
def patient():
    cursor.execute("SELECT * FROM patient")
    data = cursor.fetchall()
    return render_template('patient.html', patients=data, my_appointments=None)

@app.route('/patient_appointments', methods=['POST'])
def patient_appointments():
    pid = request.form['patient_id']
    cursor.execute("SELECT * FROM patient")
    patients_data = cursor.fetchall()
    
    cursor.execute("SELECT * FROM appointment WHERE patient_id = %s", (pid,))
    my_appointments = cursor.fetchall()
    
    return render_template('patient.html', patients=patients_data, my_appointments=my_appointments, check_id=pid)


@app.route('/add_patient', methods=['POST'])
def add_patient():
    name = request.form['name']
    dob = request.form['dob']
    email = request.form['email']

    cursor.execute("INSERT INTO patient (name, dob, email) VALUES (%s,%s,%s)", (name, dob, email))
    db.commit()
    return redirect('/patient')

# ---------------- DOCTOR ----------------
@app.route('/doctor')
def doctor():
    cursor.execute("SELECT * FROM doctor")
    data = cursor.fetchall()
    return render_template('doctor.html', doctors=data)

@app.route('/add_doctor', methods=['POST'])
def add_doctor():
    name = request.form['name']
    spec = request.form['spec']
    contact = request.form['contact']

    cursor.execute("INSERT INTO doctor (name, specialization, contact_no) VALUES (%s,%s,%s)", (name, spec, contact))
    db.commit()
    return redirect('/doctor')

@app.route('/doctor_login', methods=['POST'])
def doctor_login():
    doc_id = request.form['doc_id']
    cursor.execute("SELECT * FROM doctor WHERE id = %s", (doc_id,))
    doc = cursor.fetchone()
    if doc:
        return redirect(f'/doctor_dashboard/{doc_id}')
    else:
        return redirect('/doctor')

@app.route('/doctor_dashboard/<int:doc_id>')
def doctor_dashboard(doc_id):
    cursor.execute("SELECT * FROM doctor WHERE id = %s", (doc_id,))
    doc = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) FROM appointment WHERE doc_id = %s AND status = 'Attended'", (doc_id,))
    attended_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT * FROM appointment WHERE doc_id = %s AND status = 'Accepted'", (doc_id,))
    accepted_appointments = cursor.fetchall()
    
    return render_template('doctor_dashboard.html', doctor=doc, attended_count=attended_count, accepted_appointments=accepted_appointments)

@app.route('/doctor_update_status', methods=['POST'])
def doctor_update_status():
    app_id = request.form['appointment_id']
    doc_id = request.form['doc_id']
    cursor.execute("UPDATE appointment SET status = 'Attended' WHERE id = %s", (app_id,))
    db.commit()
    return redirect(f'/doctor_dashboard/{doc_id}')

# ---------------- APPOINTMENT ----------------
@app.route('/appointment')
def appointment():
    cursor.execute("SELECT * FROM appointment")
    data = cursor.fetchall()
    
    cursor.execute("SELECT * FROM doctor")
    doctors = cursor.fetchall()
    
    return render_template('appointment.html', appointments=data, doctors=doctors)

@app.route('/add_appointment', methods=['POST'])
def add_appointment():
    pid = request.form['patient_id']
    reason = request.form['reason']
    time = request.form['time']

    cursor.execute("INSERT INTO appointment (patient_id, doc_id, appointment_time, status, reason) VALUES (%s, NULL, %s, 'Pending', %s)", (pid, time, reason))
    db.commit()
    return redirect('/patient')

@app.route('/update_appointment_status', methods=['POST'])
def update_appointment_status():
    app_id = request.form['appointment_id']
    status = request.form['status']
    doc_id = request.form.get('doc_id')
    
    if status == 'Accepted' and doc_id:
        cursor.execute("UPDATE appointment SET status = %s, doc_id = %s WHERE id = %s", (status, doc_id, app_id))
    else:
        cursor.execute("UPDATE appointment SET status = %s WHERE id = %s", (status, app_id))
        
    db.commit()
    return redirect('/appointment')

# ---------------- BILL ----------------
@app.route('/billing', methods=['GET', 'POST'])
def billing():
    if request.method == 'POST':
        pid = request.form['patient_id']
        cursor.execute("SELECT * FROM bills WHERE patient_id = %s", (pid,))
        data = cursor.fetchall()
        return render_template('billing.html', bills=data, check_id=pid)
    else:
        cursor.execute("SELECT * FROM bills")
        data = cursor.fetchall()
        return render_template('billing.html', bills=data, check_id=None)

@app.route('/add_bill', methods=['POST'])
def add_bill():
    pid = request.form['patient_id']
    treatment = request.form['treatment']
    room_charges = request.form['room_charges']

    cursor.execute("INSERT INTO bills (patient_id, treatment_name, room_charges) VALUES (%s,%s,%s)", (pid, treatment, room_charges))
    db.commit()
    
    cursor.execute("SELECT * FROM bills WHERE patient_id = %s", (pid,))
    data = cursor.fetchall()
    return render_template('billing.html', bills=data, check_id=pid)

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)