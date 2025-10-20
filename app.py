from flask import Flask,send_from_directory, render_template, redirect, url_for, flash, jsonify, session,make_response
import pyodbc
import hashlib
import os
from werkzeug.security import check_password_hash
from werkzeug.utils import safe_join
import mimetypes
from flask import send_file
import smtplib
from flask import Flask, request, jsonify
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import request
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import json
import http.client  
from fpdf import FPDF
import tempfile
from email.message import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import tempfile
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
from email.utils import formataddr
app = Flask(__name__, template_folder="Template")
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER']  = UPLOAD_FOLDER

# Ensure the 'uploads' directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Database connection configuration
server = 'SERVER\SQLEXPRESS'
database = 'FailureAnalysis'
employee_database = 'EmployeeDirectoryDB'
username = 'Amit'
password = 'Amit@1215'

def get_db_connection():
    """Establish and return a database connection."""
    try:
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password}'
        )
        return conn
    except pyodbc.Error as e:
        print(f"Error connecting to the database: {e}")
        return None  # Return None if the connection fails




        
def get_employee_db_connection():
    try:
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={employee_database};'
            f'UID={username};'
            f'PWD={password}'
        )
        return conn
    except pyodbc.Error as e:
        print(f"Error connecting to the database: {e}")
        return None  # Return None if the connection fails

def hash_password(password):
    """Hash the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def home():
    """Home Page"""
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return render_template('register.html')

        hashed_password = hash_password(password)

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM Users WHERE Email = ?", (username,))
                existing_user = cursor.fetchone()

                if existing_user:
                    # ⚡ Show message immediately (no redirect)
                    flash("This email is already registered. Please login.", "warning")
                    return render_template('register.html')

                cursor.execute("""
                    INSERT INTO Users (Email, Password, CreatedAt, Role)
                    VALUES (?, ?, GETDATE(), 'User')
                """, (username, hashed_password))
                conn.commit()

                # ⚡ Show success immediately
                flash("Registration successful! Please login.", "success")
                return render_template('register.html')

            except Exception as e:
                flash(f"An error occurred: {e}", "danger")
                return render_template('register.html')
            finally:
                conn.close()
        else:
            flash("Database connection failed.", "danger")
            return render_template('register.html')

    return render_template('register.html')









@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['email']
        password = request.form['password']
        hashed_password = hash_password(password)

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT Email, Role FROM Users WHERE LOWER(Email) = LOWER(?) AND Password = ?", (username, hashed_password))
                user = cursor.fetchone()

                if user:
                    session["user_email"] = user[0]
                    session["user_role"] = user[1]

                    print(f"✅ Logged in as: {user[0]}")  # 👈 Prints logged-in email

                    next_page = request.form.get('next') or request.args.get('next')
                    print(f"🔗 Redirecting to next: {next_page}")  # Debug

                    if next_page:
                        return redirect(next_page)
                    elif user[0].lower() == "admin12@gmail.com":
                        return redirect('/dashboard')
                    else:
                        return redirect('/dashboard_1')
                else:
                    flash("Invalid email or password.", "danger")
            except Exception as e:
                flash(f"An error occurred: {str(e)}", "danger")
            finally:
                conn.close()
        else:
            flash("Database connection failed.", "danger")

    return render_template('login.html')



@app.route('/dashboard')
def dashboard():
    if "user_email" not in session:
        return redirect('/login')
    return render_template("dashboard.html", user_email=session.get("user_email"))

@app.route('/dashboard_1')
def dashboard_1():
    if "user_email" not in session:
        return redirect('/login')
    return render_template("dashboard.html")



@app.route('/fa')
def create_fa():
   
    return render_template("create-fa.html")



from datetime import datetime
from flask import request, redirect, url_for, flash, session
import threading

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        data = request.form

        # Multi-select fields as CSV strings
        complaints = ', '.join(data.getlist('complaint'))
        points_of_defect = ', '.join(data.getlist('point_of_defect'))

        # Logged-in user email from session
        submitted_email = session.get("user_email", None)
        print(f"📧 Logged-in user email: {submitted_email}")

        # -------------------------------
        # Safe conversion for numeric fields
        # -------------------------------
        # Quantity → INT
        quantity = data.get('quantity', '').strip()
        try:
            quantity = int(quantity) if quantity else 0
        except ValueError:
            quantity = 0

        # Defect Rate → FLOAT/DECIMAL
        defect_rate = data.get('defect_rate', '').strip()
        try:
            defect_rate = float(defect_rate) if defect_rate else None
        except ValueError:
            defect_rate = None

        # -------------------------------
        # Build database values tuple
        # -------------------------------
        values = (
            data.get('customer', ''), data.get('contact_person', ''), data.get('tel', ''),
            data.get('email', ''), data.get('cust_ref', ''), data.get('cust_location', ''),
            data.get('suchi_originator', ''), data.get('date_received', ''), data.get('sent_to', ''),
            data.get('suchi_pn', ''), data.get('datecode', ''), data.get('customer_pn', ''),
            data.get('serial', ''), quantity, data.get('invoice', ''), complaints,
            data.get('defect_comments', ''), points_of_defect,
            data.get('defect_point_comments', ''), defect_rate,
            data.get('application', ''), data.get('remarks', ''), submitted_email
        )

        insert_query = """
        INSERT INTO FailureAnalysisRequests (
            customer, contact_person, tel, email, cust_ref, cust_location,
            suchi_originator, date_received, sent_to, suchi_pn, datecode, customer_pn,
            serial, quantity, invoice, complaint, defect_comments, point_of_defect,
            defect_point_comments, defect_rate, application, remarks, submitted_by_email
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Execute insert and get inserted ID
            cursor.execute(insert_query, values)
            request_id_row = cursor.fetchone()
            request_id = request_id_row[0] if request_id_row else None
            print(f"📦 Inserted Request ID: {request_id}")

            conn.commit()

            if not request_id:
                flash("Error: Could not retrieve the new request ID.", "danger")
                return redirect(url_for('dashboard'))

            # Build data_dict for PDF/email
            data_dict = {
                "id": request_id,
                "customer": data.get("customer", ""),
                "contact_person": data.get("contact_person", ""),
                "tel": data.get("tel", ""),
                "email": data.get("email", ""),
                "cust_ref": data.get("cust_ref", ""),
                "cust_location": data.get("cust_location", ""),
                "suchi_originator": data.get("suchi_originator", ""),
                "date_received": data.get("date_received", ""),
                "sent_to": data.get("sent_to", ""),
                "suchi_pn": data.get("suchi_pn", ""),
                "datecode": data.get("datecode", ""),
                "customer_pn": data.get("customer_pn", ""),
                "serial": data.get("serial", ""),
                "quantity": quantity,
                "invoice": data.get("invoice", ""),
                "defect_comments": data.get("defect_comments", ""),
                "defect_point_comments": data.get("defect_point_comments", ""),
                "defect_rate": defect_rate,
                "application": data.get("application", ""),
                "remarks": data.get("remarks", ""),
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # ----------------------------
            # Background thread for PDF + Email
            # ----------------------------
            def process_pdf_and_email(data_dict, complaints, points_of_defect, request_id):
                try:
                    pdf_path = generate_failure_pdf(data_dict, complaints, points_of_defect)
                    rohan_email = get_email_by_name("Rohan Paul")
                    if rohan_email:
                        send_failure_email_smtp(rohan_email, pdf_path, request_id)
                        print(f"✅ Email sent to Rohan for request {request_id}")
                except Exception as e:
                    print(f"❌ Error in background PDF/email: {e}")

            threading.Thread(
                target=process_pdf_and_email,
                args=(data_dict, complaints, points_of_defect, request_id)
            ).start()

            # Flash success immediately
            flash("Form submitted successfully! PDF/email are being processed.", "success")

        except Exception as e:
            print(f"❌ Error in submit: {e}")
            flash(f"Error: {str(e)}", "danger")
        finally:
            if conn:
                conn.close()
            print("✅ DB connection closed.")

        return redirect(url_for('dashboard'))




@app.route('/report')
def report():
    return render_template("masterlist.html")


@app.route('/masterlist')
def masterlist():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch only required columns with status (default 'Open' if NULL)
    query = """
    SELECT 
        r.id, 
        r.suchi_originator, 
        r.complaint, 
        r.defect_comments, 
        COALESCE(f.status, 'Open') AS status  -- Default status to 'Open'
    FROM FailureAnalysis.dbo.FailureAnalysisRequests r
    LEFT JOIN FailureAnalysis.dbo.FileStatus f ON r.id = f.id
    """
    
    cursor.execute(query)
    records = cursor.fetchall()
    conn.close()
    
    return render_template('masterlist.html', records=records)





@app.route('/details/<int:request_id>')
def details(request_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT * FROM FailureAnalysis.dbo.FailureAnalysisRequests WHERE id = ?
    """
    cursor.execute(query, (request_id,))
    record = cursor.fetchone()
    conn.close()

    if not record:
        return "❌ Request not found", 404

    return render_template('details.html', record=record, request_id=request_id)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'uploaded_file' not in request.files or 'request_id' not in request.form:
        return "❌ Missing file or request_id", 400

    file = request.files['uploaded_file']
    request_id = int(request.form['request_id'])  # Get ID from hidden field
    print(f"📦 Uploading file for Request ID: {request_id}")

    if file.filename == '':
        return "❌ No selected file", 400

    if file:
        file_data = file.read()
        file_name = file.filename

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # ✅ Insert using request_id as id
            query = """
                INSERT INTO UploadedFiles (id, file_name, file_data, uploaded_at)
                VALUES (?, ?, ?, GETDATE())
            """
            cursor.execute(query, (request_id, file_name, file_data))
            conn.commit()

            print(f"📁 File '{file_name}' uploaded successfully for Request ID: {request_id}")

            # 🔥 Fetch submitter's email from FailureAnalysisRequests
            cursor.execute("""
                SELECT submitted_by_email
                FROM FailureAnalysisRequests
                WHERE id = ?
            """, (request_id,))
            result = cursor.fetchone()

            if result and result[0]:
                recipient_email = result[0]
                print(f"📧 Sending confirmation to: {recipient_email}")

                deep_link = f"http://192.168.1.21:5006/login?next=/details/{request_id}"
                send_report_submission_email(recipient_email, request_id, deep_link)
                print("✅ Confirmation email sent.")
            else:
                print("⚠️ No submitted_by_email found for id =", request_id)

            cursor.close()
            conn.close()

            # 👇 Changed the success message here
            return jsonify({'message': '📁 File uploaded successfully and email sent!'}), 200

        except Exception as e:
            print(f"❌ Error in upload_file: {e}")
            return jsonify({'error': str(e)}), 500




def send_report_submission_email(recipient, request_id, deep_link):
    try:
        print(f"📤 Sending report submission email to: {recipient}")

        msg = EmailMessage()
        msg['Subject'] = f"Report Submitted for Failure Analysis Request #{request_id}"
        msg['From'] = 'Failure Analysis <rohanpaul927@gmail.com>'
        msg['To'] = recipient

        # Plain text
        msg.set_content(f"""\
Your report for Failure Analysis Request #{request_id} has been submitted.

You can view details here:
{deep_link}
""")

        # HTML version
        msg.add_alternative(f"""\
<html>
  <body>
    <p>Hello,</p>
    <p>Your report for Failure Analysis Request <strong>#{request_id}</strong> has been successfully submitted.</p>
    <p>
      <a href="{deep_link}" style="
        display:inline-block;
        padding:10px 20px;
        background-color:#28a745;
        color:#fff;
        text-decoration:none;
        border-radius:5px;">
        View Request Details
      </a>
    </p>
    <p>If the button doesn’t work, use this link:<br>
    <a href="{deep_link}">{deep_link}</a></p>
  </body>
</html>
""", subtype='html')

        # Send via SMTP
        smtp_server = "smtp-relay.brevo.com"
        smtp_port = 587
        smtp_user = "8843e2001@smtp-brevo.com"
        smtp_password = "ndjfLytYKO7ZIarw"

        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)

        print("✅ Report submission email sent successfully.")

    except Exception as e:
        print(f"❌ Error sending email: {e}")



@app.route('/download/<int:file_id>')
def download_file(file_id):
    # Retrieve file data from the database by file ID
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT file_name, file_data FROM UploadedFiles WHERE id = ?"
    cursor.execute(query, (file_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        file_name, file_data = row
        return (file_data, {'Content-Disposition': f'attachment; filename={file_name}'})
    else:
        return "File not found"






@app.route("/view-file/<int:file_id>")
def view_file(file_id):
    try:
        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Fetch file name and binary data
        query = "SELECT file_name, file_data FROM UploadedFiles WHERE id = ?"
        cursor.execute(query, (file_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if not result:
            return "File not found in database.", 404

        file_name, file_data = result  # Unpacking results

        # Guess MIME type
        mime_type, _ = mimetypes.guess_type(file_name)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Return file content
        response = make_response(file_data)
        response.headers["Content-Type"] = mime_type
        response.headers["Content-Disposition"] = f'inline; filename="{file_name}"'
        return response

    except Exception as e:
        return f"An error occurred: {str(e)}", 500










@app.route('/update-status', methods=['POST'])
def update_status():
    request_id = request.json.get('id')  # Request ID from frontend
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch customer email
        query_email = "SELECT email FROM FailureAnalysis.dbo.FailureAnalysisRequests WHERE id = ?"
        cursor.execute(query_email, (request_id,))
        customer_email = cursor.fetchone()

        if not customer_email:
            return jsonify({'error': 'Customer email not found'}), 404

        # Check if the request ID exists in FileStatus
        query = "SELECT id FROM FileStatus WHERE id = ?"
        cursor.execute(query, (request_id,))
        file_status_record = cursor.fetchone()

        if not file_status_record:
            # Insert a new entry if it doesn't exist
            insert_query = "INSERT INTO FileStatus (id, status, updated_at) VALUES (?, 'Closed', GETDATE())"
            cursor.execute(insert_query, (request_id,))
        else:
            # Update existing entry
            update_query = "UPDATE FileStatus SET status = 'Closed', updated_at = GETDATE() WHERE id = ?"
            cursor.execute(update_query, (file_status_record[0],))

        conn.commit()
        conn.close()

        # 👇 Changed only this message
        return jsonify({'message': 'The failure analysis closed successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_email_by_name(name):
    conn = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={employee_database};'
        f'UID={username};'
        f'PWD={password}'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM dbo.Employees WHERE name = ?", (name,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

# Generate PDF from form data

import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepInFrame
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from xml.sax.saxutils import escape

def generate_failure_pdf(data_dict, complaints, points_of_defect):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(temp_file.name, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)

    styles = getSampleStyleSheet()
    heading_style = styles['Heading3']
    normal_style = ParagraphStyle(
        'Normal',
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        spaceAfter=4
    )

    elements = []

    def add_section_title(title):
        elements.append(Paragraph(f"<b>{escape(title)}</b>", heading_style))
        elements.append(Spacer(1, 10))

    def wrap_text(text):
        safe = escape(text or "").replace('\n', '<br/>')
        para = Paragraph(safe, normal_style)
        return KeepInFrame(0, 0, [para], hAlign='LEFT')

    def build_table(data):
        table = Table(data, colWidths=[2.2 * inch, 4.8 * inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ]))
        return table

    # 🔹 Customer Information
    add_section_title("Customer Information")
    customer_data = [
        ["Request ID", data_dict.get("id", "")],
        ["Customer", data_dict.get("customer", "")],
        ["Contact Person", data_dict.get("contact_person", "")],
        ["Tel No.", data_dict.get("tel", "")],
        ["Email Address", data_dict.get("email", "")],
        ["Cust Ref. No.", data_dict.get("cust_ref", "")],
        ["Customer Location", data_dict.get("cust_location", "")],
        ["Suchi Originator", data_dict.get("suchi_originator", "")],
        ["Date Suchi 1st Rec'd", data_dict.get("date_received", "")],
        ["Sent To", data_dict.get("sent_to", "")],
    ]
    elements.append(build_table(customer_data))
    elements.append(Spacer(1, 15))

    # 🔹 Device Information
    add_section_title("Device Information")
    device_data = [
        ["Suchi PN", data_dict.get("suchi_pn", "")],
        ["Datecode", data_dict.get("datecode", "")],
        ["Customer PN", data_dict.get("customer_pn", "")],
        ["Lot/Serial#", data_dict.get("serial", "")],
        ["Quantity", data_dict.get("quantity", "")],
        ["DN/Invoice#", data_dict.get("invoice", "")],
    ]
    elements.append(build_table(device_data))
    elements.append(Spacer(1, 15))

    # 🔹 Defect Information
    add_section_title("Defect Information")
    defect_data = [
        ["Type(s) of Failure", wrap_text(complaints)],
        ["Failure Comments", wrap_text(data_dict.get("defect_comments", ""))],
        ["Point(s) of Defect", wrap_text(points_of_defect)],
        ["Point of Defect Comments", wrap_text(data_dict.get("defect_point_comments", ""))],
        ["Defect Rate", data_dict.get("defect_rate", "")],
        ["Application", data_dict.get("application", "")],
        ["Remarks/Other Data", wrap_text(data_dict.get("remarks", ""))],
    ]
    elements.append(build_table(defect_data))
    elements.append(Spacer(1, 15))


    # 🔹 Submission Info (optional)
    if data_dict.get("submitted_at"):
        add_section_title("Submission Info")
        elements.append(Paragraph(f"<b>Submitted At:</b> {escape(data_dict['submitted_at'])}", normal_style))
        elements.append(Spacer(1, 10))

    doc.build(elements)
    return temp_file.name




def send_failure_email_smtp(recipient, pdf_path, request_id):
    try:
        print(f"📧 Preparing to send email for Request ID: {request_id} to {recipient}")

        msg = EmailMessage()
        msg['Subject'] = f'Failure Analysis Request #{request_id}'
        msg['From'] = formataddr(('Failure Analysis', 'failureanalysis@suchisemicon.site'))  # ✅ Custom sender
        msg['To'] = recipient
        msg['Reply-To'] = 'rohanpaul927@gmail.com'  # ✅ Replies go to your Gmail

        # ✅ Deep link (after login redirect to /details/<request_id>)
        deep_link = f"http://192.168.1.21:5006/login?next=/details/{request_id}"
        print(f"🔗 Deep link for email: {deep_link}")

        # Plain text version
        msg.set_content(f"""
Please find attached the Failure Analysis Request #{request_id}.

To view the request details, click the link below:
{deep_link}
""")

        # HTML version with clickable button
        msg.add_alternative(f"""
<html>
  <body>
    <p>Please find attached the Failure Analysis Request <strong>#{request_id}</strong>.</p>
    <p>
      <a href="{deep_link}" style="
        display:inline-block;
        padding:10px 20px;
        background-color:#007bff;
        color:#fff;
        text-decoration:none;
        border-radius:5px;">
        View Request Details
      </a>
    </p>
    <p>If the button doesn't work, use this link:<br>
    <a href="{deep_link}">{deep_link}</a></p>
  </body>
</html>
""", subtype='html')

        # Attach PDF
        print(f"📎 Attaching PDF: {pdf_path}")
        with open(pdf_path, 'rb') as f:
            file_data = f.read()
            file_name = f'FailureRequest_{request_id}.pdf'
        msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

        # SMTP settings (Brevo or GoDaddy)
        smtp_server = "smtp-relay.brevo.com"          # Brevo SMTP server
        smtp_port = 587                               # TLS Port
        smtp_user = "8843e2001@smtp-brevo.com"        # Brevo API user
        smtp_password = "ndjfLytYKO7ZIarw"            # Brevo API key

        print("📤 Connecting to SMTP server...")
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.set_debuglevel(1)
            smtp.ehlo()
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)

        print("✅ Email sent successfully.")

    except Exception as e:
        print(f"❌ Error sending email: {e}")




@app.route('/failure-requests')
def failure_requests():
    search_id = request.args.get('search_id', '').strip()
    print(f"Search ID received: {search_id}")

    conn = pyodbc.connect(get_db_connection())
    cursor = conn.cursor()

    query = """
        SELECT id, suchi_originator, complaint, defect_comments, status
        FROM FailureAnalysis.dbo.FailureAnalysisRequests
    """

    if search_id:
        query += " WHERE id = ?"
        cursor.execute(query, (search_id,))
    else:
        cursor.execute(query)

    records = cursor.fetchall()
    conn.close()

    print(f"Total Records Found: {len(records)}")
    return render_template('masterlist.html', records=records)



@app.route('/upload-report/<int:request_id>', methods=['GET', 'POST'])
def upload_report(request_id):
    if request.method == 'POST':
        uploaded_file = request.files.get('report_file')
        if uploaded_file:
            file_data = uploaded_file.read()
            file_name = uploaded_file.filename

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO [FailureAnalysis].[dbo].[UploadedFiles]
                (file_name, file_data, uploaded_at)
                VALUES (?, ?, GETDATE())
            """, (file_name, file_data))
            conn.commit()
            cursor.close()
            conn.close()

            flash("Report uploaded successfully!", "success")
            return redirect(url_for('dashboard'))

    return render_template('upload_report.html', request_id=request_id)

    

# Brevo mail config
sender_name = "Failure Analysis System"
sender_email = "failureanalysis@suchisemicon.site"
smtp_username = "8843e2001@smtp-brevo.com"
smtp_password = "ndjfLytYKO7ZIarw"
smtp_server = "smtp-relay.brevo.com"
smtp_port = 587

# Token generator
serializer = URLSafeTimedSerializer(app.secret_key)

def generate_reset_token(email):
    return serializer.dumps(email, salt='password-reset-salt')

def send_reset_email(to_email, reset_url):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Password Reset Request"
    msg['From'] = f"{sender_name} <{sender_email}>"
    msg['To'] = to_email

    html_content = f"""
    <html>
        <body>
            <p>Hello,</p>
            <p>You requested a password reset. Click the link below to reset your password:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server_smtp = smtplib.SMTP(smtp_server, smtp_port)
        server_smtp.starttls()
        server_smtp.login(smtp_username, smtp_password)
        server_smtp.sendmail(sender_email, to_email, msg.as_string())
        server_smtp.quit()
        print(f"Reset email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

# ================== Forgot Password Route ==================
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    # 🧹 Clear any previous flash messages (from login failures etc.)
    session.pop('_flashes', None)

    if request.method == 'POST':
        email = request.form['email'].strip()

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Email FROM [FailureAnalysis].[dbo].[Users] WHERE Email = ?", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                token = generate_reset_token(email)
                reset_url = url_for('reset_password', token=token, _external=True)
                send_reset_email(email, reset_url)

        # Always show generic message
        flash("If this email exists, a password reset link has been sent.", "info")
        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')



# ================== Reset Password Route ==================
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash("The reset link is invalid or has expired.", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm-password']

        if new_password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('reset_password', token=token))

        hashed_password = hash_password(new_password)

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE [FailureAnalysis].[dbo].[Users] SET Password=? WHERE Email=?",
                (hashed_password, email)
            )
            conn.commit()
            cursor.close()
            conn.close()

        flash("Your password has been reset successfully!", "success")
        # ✅ Redirect to a new route so the success message shows once
        return redirect(url_for('login'))

    # ✅ Ensure GET request does not re-flash anything
    return render_template('reset_password.html')




if __name__ == "__main__":
    from waitress import serve
    serve(app, host='0.0.0.0', port=5006)