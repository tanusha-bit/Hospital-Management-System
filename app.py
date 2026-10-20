import hmac
import os

from flask import Flask, abort, flash, render_template, request, redirect, session
# Version 1: Initial HMS implementation
from flask import Flask, render_template, request, redirect
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("HOSPITAL_SECRET_KEY")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

ADMIN_USERNAME = os.environ.get("HOSPITAL_ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("HOSPITAL_ADMIN_PASSWORD")
STAKEHOLDER_TABLES = {
    "patient": "patient",
    "doctor": "doctor",
    "nurse": "nurse",
    "pharmacist": "pharmacist",
}

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Crime@123",
    database="hospital"
)

cursor = db.cursor()


def create_tables():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            dob VARCHAR(50) NOT NULL,
            email VARCHAR(255) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            specialization VARCHAR(255) NOT NULL,
            contact_no VARCHAR(20) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nurse (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            specialization VARCHAR(255) NOT NULL,
            contact_no VARCHAR(20) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pharmacist (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            contact_no VARCHAR(20) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointment (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT,
            doc_id INT,
            appointment_time VARCHAR(100) NOT NULL,
            status VARCHAR(50) DEFAULT 'Pending',
            reason VARCHAR(255),
            FOREIGN KEY (patient_id) REFERENCES patient(id) ON DELETE CASCADE,
            FOREIGN KEY (doc_id) REFERENCES doctor(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT,
            treatment_name VARCHAR(255) NOT NULL,
            room_charges VARCHAR(100) NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patient(id) ON DELETE CASCADE
        )
    """)

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stakeholder_account (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role VARCHAR(20) NOT NULL,
            stakeholder_id INT NOT NULL,
            username VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            UNIQUE KEY unique_stakeholder_account (role, stakeholder_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nurse_patient (
            nurse_id INT NOT NULL,
            patient_id INT NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (nurse_id, patient_id),
            FOREIGN KEY (nurse_id) REFERENCES nurse(id) ON DELETE CASCADE,
            FOREIGN KEY (patient_id) REFERENCES patient(id) ON DELETE CASCADE
        )
    """)

    db.commit()


create_tables()


@app.before_request
def require_role():
    public_endpoints = {
        "index",
        "admin_login",
        "stakeholder_login",
        "stakeholder_register",
        "admin_logout",
        "static",
    }
    if request.endpoint in public_endpoints:
        return None

    if not app.secret_key:
        return (
            "Authentication is not configured. Set HOSPITAL_SECRET_KEY.",
            503,
        )

    role = session.get("role")
    endpoint = request.endpoint
    role_endpoints = {
        "patient_portal": "patient",
        "add_appointment": "patient",
        "doctor_dashboard": "doctor",
        "doctor_update_status": "doctor",
        "add_prescription": "doctor",
        "doctor_generate_invoice": "doctor",
        "pharmacist_dashboard": "pharmacist",
        "add_inventory": "pharmacist",
        "update_stock": "pharmacist",
        "nurse_dashboard": "nurse",
        "add_patient_care": "nurse",
        "my_billing": "patient",
        "view_invoice": {"admin", "patient"},
        "download_invoice": {"admin", "patient"},
    }
    required_role = role_endpoints.get(endpoint)
    if isinstance(required_role, str):
        allowed_roles = {required_role}
    elif required_role:
        allowed_roles = required_role
    else:
        allowed_roles = {"admin"}
    if role not in allowed_roles:
        if role in STAKEHOLDER_TABLES:
            return abort(403)
        if role is None and isinstance(required_role, str):
            return redirect(f"/login/{required_role}")
        return redirect("/admin_login" if role is None else "/")

    return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login/<role>', methods=['GET', 'POST'])
def stakeholder_login(role):
    if role not in STAKEHOLDER_TABLES:
        return abort(404)

    if not app.secret_key:
        return "Authentication is not configured. Set HOSPITAL_SECRET_KEY.", 503

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        cursor.execute(
            "SELECT stakeholder_id, password_hash FROM stakeholder_account "
            "WHERE role = %s AND username = %s",
            (role, username),
        )
        account = cursor.fetchone()
        if account and check_password_hash(account[1], password):
            session.clear()
            session['role'] = role
            session['stakeholder_id'] = account[0]
            return redirect(f'/{role}_dashboard/{account[0]}')
        error = "Invalid username or password."

    return render_template('stakeholder_login.html', role=role.title(), error=error)


@app.route('/register/<role>', methods=['GET', 'POST'])
def stakeholder_register(role):
    if role not in STAKEHOLDER_TABLES:
        return abort(404)

    if not app.secret_key:
        return "Authentication is not configured. Set HOSPITAL_SECRET_KEY.", 503

    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        profile = {}

        if role == 'patient':
            profile = {
                'dob': request.form.get('dob', '').strip(),
                'email': request.form.get('email', '').strip(),
            }
        elif role in {'doctor', 'nurse'}:
            profile = {
                'specialization': request.form.get('specialization', '').strip(),
                'contact': request.form.get('contact', '').strip(),
            }
        else:
            profile = {'contact': request.form.get('contact', '').strip()}

        valid_lengths = (
            len(name) <= 255
            and len(username) <= 100
            and all(len(value) <= limit for value, limit in (
                (profile.get('dob', ''), 50),
                (profile.get('email', ''), 255),
                (profile.get('specialization', ''), 255),
                (profile.get('contact', ''), 20),
            ))
        )
        if (
            not name
            or not username
            or any(not value for value in profile.values())
            or len(password) < 12
            or password != password_confirm
            or not valid_lengths
        ):
            error = (
                "Complete all fields, use a password of at least 12 characters, "
                "and make sure both passwords match."
            )
        else:
            cursor.execute(
                "SELECT id FROM stakeholder_account WHERE username = %s",
                (username,),
            )
            if cursor.fetchone():
                error = "That username is already in use."
            else:
                table = STAKEHOLDER_TABLES[role]
                if role == 'patient':
                    insert_record = (
                        "INSERT INTO patient (name, dob, email) VALUES (%s, %s, %s)",
                        (name, profile['dob'], profile['email']),
                    )
                elif role in {'doctor', 'nurse'}:
                    insert_record = (
                        f"INSERT INTO {table} (name, specialization, contact_no) "
                        "VALUES (%s, %s, %s)",
                        (name, profile['specialization'], profile['contact']),
                    )
                else:
                    insert_record = (
                        "INSERT INTO pharmacist (name, contact_no) VALUES (%s, %s)",
                        (name, profile['contact']),
                    )

                try:
                    cursor.execute(*insert_record)
                    stakeholder_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO stakeholder_account "
                        "(role, stakeholder_id, username, password_hash) "
                        "VALUES (%s, %s, %s, %s)",
                        (role, stakeholder_id, username, generate_password_hash(password)),
                    )
                    db.commit()
                except mysql.connector.IntegrityError as exc:
                    db.rollback()
                    if exc.errno != 1062:
                        raise
                    error = "That username is already in use."
                else:
                    flash("Registration complete. Sign in with your new credentials.", "success")
                    return redirect(f'/login/{role}')

    return render_template(
        'stakeholder_register.html',
        role=role.title(),
        error=error,
        form_data=request.form,
    ), 400 if error else 200


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    auth_configured = bool(app.secret_key and ADMIN_USERNAME and ADMIN_PASSWORD)
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if (
            app.secret_key
            and ADMIN_USERNAME is not None
            and ADMIN_PASSWORD is not None
            and hmac.compare_digest(username, ADMIN_USERNAME)
            and hmac.compare_digest(password, ADMIN_PASSWORD)
        ):
            session.clear()
            session['role'] = 'admin'
            return redirect('/operator')

        return render_template(
            'admin_login.html',
            auth_configured=auth_configured,
            error='Invalid credentials.' if auth_configured else None,
        ), 401 if auth_configured else 503

    return render_template('admin_login.html', auth_configured=auth_configured)


@app.route('/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return redirect('/')


# ---------------- OPERATOR ----------------
@app.route('/operator')
def operator():
    return render_template('operator.html')


def render_admin_accounts(error=None):
    stakeholders = []
    for role, table in STAKEHOLDER_TABLES.items():
        cursor.execute(f"SELECT id, name FROM {table} ORDER BY name")
        stakeholders.extend((role, row[0], row[1]) for row in cursor.fetchall())

    cursor.execute(
        "SELECT role, stakeholder_id, username FROM stakeholder_account ORDER BY role, username"
    )
    accounts = cursor.fetchall()
    cursor.execute("""
        SELECT np.nurse_id, n.name, np.patient_id, p.name
        FROM nurse_patient np
        JOIN nurse n ON n.id = np.nurse_id
        JOIN patient p ON p.id = np.patient_id
        ORDER BY n.name, p.name
    """)
    nurse_assignments = cursor.fetchall()
    cursor.execute("SELECT id, name FROM nurse ORDER BY name")
    nurses = cursor.fetchall()
    cursor.execute("SELECT id, name FROM patient ORDER BY name")
    patients = cursor.fetchall()
    return render_template(
        'admin_accounts.html',
        stakeholders=stakeholders,
        accounts=accounts,
        nurse_assignments=nurse_assignments,
        nurses=nurses,
        patients=patients,
        error=error,
    )


@app.route('/admin/accounts')
def admin_accounts():
    return render_admin_accounts()


@app.route('/admin/accounts/create', methods=['POST'])
def create_stakeholder_account():
    role = request.form.get('role', '')
    stakeholder_id = request.form.get('stakeholder_id', '')
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if role not in STAKEHOLDER_TABLES or not stakeholder_id.isdigit() or not username or len(password) < 12:
        return render_admin_accounts(
            "Choose a valid stakeholder, enter a username, and use a password of at least 12 characters."
        ), 400

    table = STAKEHOLDER_TABLES[role]
    cursor.execute(f"SELECT id FROM {table} WHERE id = %s", (stakeholder_id,))
    if not cursor.fetchone():
        return render_admin_accounts("The selected stakeholder record does not exist."), 404

    cursor.execute(
        "SELECT id FROM stakeholder_account WHERE username = %s OR (role = %s AND stakeholder_id = %s)",
        (username, role, stakeholder_id),
    )
    if cursor.fetchone():
        return render_admin_accounts("That username or stakeholder account is already in use."), 409

    cursor.execute(
        "INSERT INTO stakeholder_account (role, stakeholder_id, username, password_hash) "
        "VALUES (%s, %s, %s, %s)",
        (role, stakeholder_id, username, generate_password_hash(password)),
    )
    db.commit()
    return redirect('/admin/accounts')


@app.route('/admin/assign_nurse', methods=['POST'])
def assign_nurse():
    nurse_id = request.form.get('nurse_id', '')
    patient_id = request.form.get('patient_id', '')
    if not nurse_id.isdigit() or not patient_id.isdigit():
        return render_admin_accounts("Select a valid nurse and patient."), 400

    cursor.execute("SELECT id FROM nurse WHERE id = %s", (nurse_id,))
    nurse_record = cursor.fetchone()
    cursor.execute("SELECT id FROM patient WHERE id = %s", (patient_id,))
    patient_record = cursor.fetchone()
    if not nurse_record or not patient_record:
        return render_admin_accounts("The selected nurse or patient record does not exist."), 404

    cursor.execute(
        "INSERT IGNORE INTO nurse_patient (nurse_id, patient_id) VALUES (%s, %s)",
        (nurse_id, patient_id),
    )
    db.commit()
    return redirect('/admin/accounts')


# ---------------- PATIENT ----------------
@app.route('/patient')
def patient():
    cursor.execute("SELECT * FROM patient")
    data = cursor.fetchall()
    return render_template('patient.html', patients=data, my_appointments=None)


@app.route('/patient_dashboard/<int:patient_id>')
def patient_portal(patient_id):
    if patient_id != session.get('stakeholder_id'):
        return abort(403)

    cursor.execute("SELECT * FROM patient WHERE id = %s", (patient_id,))
    patient_record = cursor.fetchone()
    if not patient_record:
        return abort(404)

    cursor.execute(
        "SELECT * FROM appointment WHERE patient_id = %s ORDER BY id DESC",
        (patient_id,),
    )
    appointments = cursor.fetchall()
    cursor.execute("SELECT * FROM bills WHERE patient_id = %s ORDER BY id DESC", (patient_id,))
    bills = cursor.fetchall()
    return render_template(
        'patient_dashboard.html',
        patient=patient_record,
        appointments=appointments,
        bills=bills,
    )

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

@app.route('/doctor_dashboard/<int:doc_id>')
def doctor_dashboard(doc_id):
    if doc_id != session.get('stakeholder_id'):
        return abort(403)

    cursor.execute("SELECT * FROM doctor WHERE id = %s", (doc_id,))
    doc = cursor.fetchone()
    if not doc:
        return abort(404)

    cursor.execute("SELECT COUNT(*) FROM appointment WHERE doc_id = %s AND status = 'Attended'", (doc_id,))
    attended_count = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM appointment WHERE doc_id = %s AND status = 'Accepted' ORDER BY id DESC", (doc_id,))
    accepted_appointments = cursor.fetchall()

    cursor.execute("""
        SELECT p.id, p.patient_id, pa.name AS patient_name, p.medicine_name, p.dosage, p.instructions, p.created_at
        FROM prescription p
        JOIN patient pa ON pa.id = p.patient_id
        WHERE p.doctor_id = %s
        ORDER BY p.created_at DESC
    """, (doc_id,))
    prescriptions = cursor.fetchall()

    return render_template('doctor_dashboard.html', doctor=doc, attended_count=attended_count,
                           accepted_appointments=accepted_appointments, prescriptions=prescriptions)


@app.route('/doctor_update_status', methods=['POST'])
def doctor_update_status():
    app_id = request.form['appointment_id']
    doc_id = session['stakeholder_id']
    cursor.execute(
        "UPDATE appointment SET status = 'Attended' "
        "WHERE id = %s AND doc_id = %s AND status = 'Accepted'",
        (app_id, doc_id),
    )
    db.commit()
    return redirect(f'/doctor_dashboard/{doc_id}')


@app.route('/add_prescription', methods=['POST'])
def add_prescription():
    patient_id = request.form['patient_id']
    doc_id = session['stakeholder_id']
    medicine_name = request.form['medicine_name']
    dosage = request.form['dosage']
    instructions = request.form['instructions']

    cursor.execute(
        "SELECT id FROM appointment WHERE patient_id = %s AND doc_id = %s "
        "AND status IN ('Accepted', 'Attended') LIMIT 1",
        (patient_id, doc_id),
    )
    if not cursor.fetchone():
        return abort(403)

    cursor.execute(
        "INSERT INTO prescription (patient_id, doctor_id, medicine_name, dosage, instructions) VALUES (%s,%s,%s,%s,%s)",
        (patient_id, doc_id, medicine_name, dosage, instructions)
    )
    db.commit()
    return redirect(f'/doctor_dashboard/{doc_id}')


@app.route('/doctor_generate_invoice', methods=['POST'])
def doctor_generate_invoice():
    doctor_id = session['stakeholder_id']
    patient_id = request.form.get('patient_id')
    treatment = request.form.get('treatment')
    room_charges = request.form.get('room_charges')

    if not patient_id or not treatment or not room_charges:
        return redirect(f'/doctor_dashboard/{doctor_id}')

    cursor.execute(
        "SELECT id FROM appointment WHERE patient_id = %s AND doc_id = %s "
        "AND status IN ('Accepted', 'Attended') LIMIT 1",
        (patient_id, doctor_id),
    )
    if not cursor.fetchone():
        return abort(403)

    cursor.execute(
        "INSERT INTO bills (patient_id, treatment_name, room_charges) VALUES (%s,%s,%s)",
        (patient_id, treatment, room_charges)
    )
    db.commit()
    return redirect(f'/doctor_dashboard/{doctor_id}')

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
    pid = session['stakeholder_id']
    reason = request.form['reason']
    time = request.form['time']

    cursor.execute("INSERT INTO appointment (patient_id, doc_id, appointment_time, status, reason) VALUES (%s, NULL, %s, 'Pending', %s)", (pid, time, reason))
    db.commit()
    return redirect(f'/patient_dashboard/{pid}')

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

# ---------------- BILL / INVOICE ----------------
@app.route('/billing', methods=['GET', 'POST'])
def billing():
    pid = request.form.get('patient_id') or request.args.get('patient_id')
    if pid:
        cursor.execute("SELECT * FROM bills WHERE patient_id = %s ORDER BY id DESC", (pid,))
        data = cursor.fetchall()
        return render_template('billing.html', bills=data, check_id=pid)

    cursor.execute("SELECT * FROM bills ORDER BY id DESC")
    data = cursor.fetchall()
    return render_template('billing.html', bills=data, check_id=None)


@app.route('/my_billing')
def my_billing():
    patient_id = session['stakeholder_id']
    cursor.execute(
        "SELECT * FROM bills WHERE patient_id = %s ORDER BY id DESC",
        (patient_id,),
    )
    return render_template('billing.html', bills=cursor.fetchall(), check_id=patient_id)


@app.route('/invoice/<int:invoice_id>')
def view_invoice(invoice_id):
    patient_id = session.get('stakeholder_id') if session.get('role') == 'patient' else None
    if patient_id is None:
        cursor.execute("SELECT * FROM bills WHERE id = %s", (invoice_id,))
    else:
        cursor.execute(
            "SELECT * FROM bills WHERE id = %s AND patient_id = %s",
            (invoice_id, patient_id),
        )
    invoice = cursor.fetchone()
    if not invoice:
        return abort(404)

    return render_template(
        'invoice_view.html',
        invoice=invoice,
        patient_id=patient_id,
        is_patient=patient_id is not None,
    )


@app.route('/download_invoice/<int:invoice_id>')
def download_invoice(invoice_id):
    patient_id = session.get('stakeholder_id') if session.get('role') == 'patient' else None
    if patient_id is None:
        cursor.execute("SELECT * FROM bills WHERE id = %s", (invoice_id,))
    else:
        cursor.execute(
            "SELECT * FROM bills WHERE id = %s AND patient_id = %s",
            (invoice_id, patient_id),
        )
    invoice = cursor.fetchone()
    if not invoice:
        return abort(404)

    html = render_template(
        'invoice_view.html',
        invoice=invoice,
        patient_id=patient_id,
        is_patient=patient_id is not None,
        is_download=True,
    )
    response = app.make_response(html)
    response.headers['Content-Disposition'] = f'attachment; filename=invoice_{invoice_id}.html'
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


@app.route('/add_bill', methods=['POST'])
def add_bill():
    doctor_id = request.form.get('doctor_id')
    pid = request.form.get('patient_id')
    treatment = request.form.get('treatment')
    room_charges = request.form.get('room_charges')

    if not doctor_id:
        return redirect('/billing')

    cursor.execute("SELECT * FROM doctor WHERE id = %s", (doctor_id,))
    if not cursor.fetchone():
        return redirect('/doctor')

    if not pid or not treatment or not room_charges:
        return redirect(f'/doctor_dashboard/{doctor_id}')

    cursor.execute("INSERT INTO bills (patient_id, treatment_name, room_charges) VALUES (%s,%s,%s)", (pid, treatment, room_charges))
    db.commit()

    return redirect(f'/doctor_dashboard/{doctor_id}')


# ---------------- PHARMACIST ----------------
@app.route('/pharmacist')
def pharmacist():
    cursor.execute("SELECT * FROM pharmacist")
    data = cursor.fetchall()
    return render_template('pharmacist.html', pharmacists=data)


@app.route('/add_pharmacist', methods=['POST'])
def add_pharmacist():
    name = request.form['name']
    contact = request.form['contact']

    cursor.execute("INSERT INTO pharmacist (name, contact_no) VALUES (%s,%s)", (name, contact))
    db.commit()
    return redirect('/pharmacist')


@app.route('/pharmacist_dashboard/<int:pharmacist_id>')
def pharmacist_dashboard(pharmacist_id):
    if pharmacist_id != session.get('stakeholder_id'):
        return abort(403)

    cursor.execute("SELECT * FROM pharmacist WHERE id = %s", (pharmacist_id,))
    pharmacist_record = cursor.fetchone()
    if not pharmacist_record:
        return abort(404)

    cursor.execute("SELECT * FROM inventory ORDER BY last_updated DESC")
    inventory = cursor.fetchall()

    cursor.execute("""
        SELECT p.patient_id, p.medicine_name, p.dosage, p.instructions, p.created_at
        FROM prescription p
        ORDER BY p.created_at DESC
    """)
    prescriptions = cursor.fetchall()

    return render_template('pharmacist_dashboard.html', pharmacist=pharmacist_record, inventory=inventory,
                           prescriptions=prescriptions)


@app.route('/add_inventory', methods=['POST'])
def add_inventory():
    medicine_name = request.form['medicine_name']
    category = request.form['category']
    stock_quantity = request.form['stock_quantity']
    unit_price = request.form['unit_price']
    pharmacist_id = session['stakeholder_id']

    cursor.execute(
        "INSERT INTO inventory (medicine_name, category, stock_quantity, unit_price) VALUES (%s,%s,%s,%s)",
        (medicine_name, category, stock_quantity, unit_price)
    )
    db.commit()
    return redirect(f'/pharmacist_dashboard/{pharmacist_id}')


@app.route('/update_stock', methods=['POST'])
def update_stock():
    inventory_id = request.form['inventory_id']
    new_quantity = request.form['new_quantity']
    pharmacist_id = session['stakeholder_id']

    cursor.execute("UPDATE inventory SET stock_quantity = %s WHERE id = %s", (new_quantity, inventory_id))
    db.commit()
    return redirect(f'/pharmacist_dashboard/{pharmacist_id}')


# ---------------- NURSE ----------------
@app.route('/nurse')
def nurse():
    cursor.execute("SELECT * FROM nurse")
    data = cursor.fetchall()
    return render_template('nurse.html', nurses=data)


@app.route('/add_nurse', methods=['POST'])
def add_nurse():
    name = request.form['name']
    spec = request.form['spec']
    contact = request.form['contact']

    cursor.execute("INSERT INTO nurse (name, specialization, contact_no) VALUES (%s,%s,%s)", (name, spec, contact))
    db.commit()
    return redirect('/nurse')


@app.route('/nurse_dashboard/<int:nurse_id>')
def nurse_dashboard(nurse_id):
    if nurse_id != session.get('stakeholder_id'):
        return abort(403)

    cursor.execute("SELECT * FROM nurse WHERE id = %s", (nurse_id,))
    nurse_record = cursor.fetchone()
    if not nurse_record:
        return abort(404)

    cursor.execute("""
        SELECT np.patient_id, p.name
        FROM nurse_patient np
        JOIN patient p ON p.id = np.patient_id
        WHERE np.nurse_id = %s
        ORDER BY p.name
    """, (nurse_id,))
    assigned_patients = cursor.fetchall()

    cursor.execute("""
        SELECT c.id, c.patient_id, p.name AS patient_name, c.nurse_id, c.care_note, c.status, c.updated_at
        FROM patient_care c
        JOIN patient p ON p.id = c.patient_id
        WHERE c.nurse_id = %s
        ORDER BY c.updated_at DESC
    """, (nurse_id,))
    care_updates = cursor.fetchall()

    return render_template('nurse_dashboard.html', nurse=nurse_record, assigned_patients=assigned_patients,
                           care_updates=care_updates)


@app.route('/add_patient_care', methods=['POST'])
def add_patient_care():
    patient_id = request.form['patient_id']
    nurse_id = session['stakeholder_id']
    care_note = request.form['care_note']
    status = request.form['status']

    cursor.execute(
        "SELECT patient_id FROM nurse_patient WHERE nurse_id = %s AND patient_id = %s",
        (nurse_id, patient_id),
    )
    if not cursor.fetchone():
        return abort(403)

    cursor.execute(
        "INSERT INTO patient_care (patient_id, nurse_id, care_note, status) VALUES (%s,%s,%s,%s)",
        (patient_id, nurse_id, care_note, status)
    )
    db.commit()
    return redirect(f'/nurse_dashboard/{nurse_id}')


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)
