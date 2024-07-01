import pandas
import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from db import insert_chq_payment, add_record, get_deduplicated_records, get_db_connection, process_excel_file
from openpyxl.utils import datetime
from werkzeug.utils import secure_filename
import os
import MySQLdb.cursors
import pandas as pd
from datetime import datetime, date
import csv
from file_upload import allowed_file, process_file, upload_files
from flask import request, jsonify
import re
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_wtf import CSRFProtect




app = Flask(__name__)
app.secret_key = 'supersecretkey'
csrf = CSRFProtect(app)
csrf.init_app(app)


# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Sample database connection
def get_db_connection():
    return pymysql.connect(host="localhost", user="root", passwd="P@ssw0rd@123", db="billing")

# Sample user class and user loader function
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    #connection = get_db_connection()
    cursor = database1.cursor()
    cursor.execute('SELECT * FROM admin_record WHERE id = %s', (user_id,))
    account = cursor.fetchone()
    if account:
        return User(id=account[0], username=account[1])
    return None






app.config['UPLOAD_FOLDER'] = 'uploads'

database1 = pymysql.connect(host="localhost", user="root", passwd="P@ssw0rd@123", db="billing")
cursor = database1.cursor()


database1 = pymysql.connect(
    host="localhost",
    user="root",
    passwd="P@ssw0rd@123",
    db="billing",
    #cursorclass=pymysql.cursors.DictCursor  # Ensure cursor returns dict
)


def insert_cheque_payments():
    insert_chq_payment("cheque_payments.xlsx")  # Call insert_chq_payment function with your filename

    return "Cheque payments inserted successfully!"


def insert_cash_payments():
    insert_chq_payment("staticFiles/uploads/cheque_payments.xlsx")  # Call insert_chq_payment function with your filename

    return "Cash payments inserted successfully!"

@app.route('/')

@app.route('/front')
def front():
    return render_template("front.html")


@app.route('/home')
@login_required
def home():
    if current_user.is_authenticated:
        return render_template('home.html')
    else:
        return redirect(url_for('login'))



@app.route('/cheque')
def cheque():
    try:
        # Create cursor within the route function
        cursor = database1.cursor()

        cursor.execute("SELECT * FROM cheque_payments")
        data = cursor.fetchall()  # Fetch all rows

        # Calculate total amount
        total_amount = sum(row[2] for row in data)

        # Calculate individual payer totals
        payer_totals = {}
        for row in data:
            payer_name = row[3]  # Assuming payer_name is in the fourth column (index 3)
            amount = row[2]       # Assuming amount is in the third column (index 2)
            if payer_name in payer_totals:
                payer_totals[payer_name] += amount
            else:
                payer_totals[payer_name] = amount

        # Close cursor after fetching data
        cursor.close()

        # Render template with data, total_amount, and payer_totals
        return render_template('cheque_payment.html', data=data, total_amount=total_amount, payer_totals=payer_totals)

    except Exception as e:
        return f"Error: {str(e)}"


@app.route('/billing')
def billing():
    return render_template("billing.html")


# Configuration for file uploads
#UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
UPLOAD_FOLDER = os.path.join('staticFiles', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xls', 'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Maximum file size: 16MB

# Ensure the upload folder exists
#if not os.path.exists(UPLOAD_FOLDER):
 #   os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_files', methods=['GET', 'POST'])
@csrf.exempt
def upload_files_route():
    return upload_files()



# load to DB


@app.route('/record', methods=['GET', 'POST'])
@csrf.exempt
@login_required
def add_record():
    msg = ''
    if request.method == 'POST':
        bill_no = request.form['bill_no']
        bill_date = request.form['bill_date']
        retailer_code = request.form['retailer_code']
        retailer_name = request.form['retailer_name']
        bill_amount = request.form['bill_amount']
        delivered = request.form['delivered']
        received_amount = request.form['received_amount']
        discount = request.form['discount']
        remaining_amount = request.form['remaining_amount']
        payment_method = request.form['payment_method']
        bank_name = request.form['bank_name']
        cheque_no = request.form['cheque_no']
        cheq_rcv_date = request.form['cheq_rcv_date']
        cheq_exp_date = request.form['cheq_exp_date']
        remaining_days = request.form['remaining_days']
        payment_closure = request.form['payment_closure']
        payment_closure_date = request.form['payment_closure_date']
        remarks = request.form['remarks']
        bounce = request.form['bounce']
        bounce1 = request.form['bounce1']
        bounce2 = request.form['bounce2']
        reason_bounce = request.form['reason_bounce']

        cursor = database1.cursor()


        cursor.execute('SELECT retailer_name FROM retailer_table WHERE retailer_code = %s', (retailer_code,))
        result = cursor.fetchone()

        if result and result[0] == retailer_name:
                if cheq_rcv_date and cheq_exp_date:
                    cheq_rcv_date_dt = datetime.strptime(cheq_rcv_date, '%Y-%m-%d')
                    cheq_exp_date_dt = datetime.strptime(cheq_exp_date, '%Y-%m-%d')
                    remaining_days = (cheq_exp_date_dt - cheq_rcv_date_dt).days

                else:
                    cheq_rcv_date = None
                    cheq_exp_date = None
                    remaining_days = None
                    cheque_no = None
                    bank_name = None

                remaining_amount = float(bill_amount) - (float(received_amount) + float(discount))


                query = '''INSERT INTO record (bill_no, bill_date, retailer_code, retailer_name, bill_amount, delivered, received_amount, discount, remaining_amount, payment_method, bank_name, cheque_no, cheq_rcv_date, cheq_exp_date, remaining_days, payment_closure, payment_closure_date, remarks, bounce, bounce1, bounce2, reason_bounce) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                values = (bill_no, bill_date, retailer_code, retailer_name, bill_amount, delivered, received_amount, discount,
                          remaining_amount, payment_method, bank_name, cheque_no, cheq_rcv_date, cheq_exp_date, remaining_days,
                          payment_closure, payment_closure_date, remarks, bounce, bounce1, bounce2, reason_bounce)
                cursor.execute(query, values)
                database1.commit()
                cursor.close()
                msg = 'Record added successfully!'
                flash(msg)
                return redirect(url_for('view_records'))

        else:
            cursor.close()
            return "Retailer code and retailer name do not match. Please check the values."

    return render_template("record1.html", msg=msg)


@app.route('/view_records')

@login_required
def view_records():
    cursor = database1.cursor()
    query = "SELECT * FROM record"
    cursor.execute(query)
    records = cursor.fetchall()
    cursor.close()
    print(records)  # Add this line to debug
    return render_template('view_records.html', records=records)



@app.route('/delete_record/<int:record_id>', methods=['POST'])
@login_required
@csrf.exempt
def delete_record(record_id):
    cursor = database1.cursor()
    query = "DELETE FROM record WHERE id = %s"
    cursor.execute(query, (record_id,))
    database1.commit()
    cursor.close()
    flash('Record deleted successfully!')
    return redirect(url_for('view_records'))


@app.route('/update_record/<int:record_id>', methods=['GET', 'POST'])
@csrf.exempt
@login_required
def update_record(record_id):

    msg = ''
    cursor = database1.cursor()
    if request.method == 'POST':
        bill_no = request.form['bill_no']
        bill_date = request.form['bill_date']
        retailer_code = request.form['retailer_code']
        retailer_name = request.form['retailer_name']
        bill_amount = request.form['bill_amount']
        delivered = request.form['delivered']
        received_amount = request.form['received_amount']
        discount = request.form['discount']
        remaining_amount = request.form['remaining_amount']
        payment_method = request.form['payment_method']
        bank_name = request.form['bank_name']
        cheque_no = request.form['cheque_no']
        cheq_rcv_date = request.form['cheq_rcv_date']
        cheq_exp_date = request.form['cheq_exp_date']
        remaining_days = request.form['remaining_days']
        payment_closure = request.form['payment_closure']
        payment_closure_date = request.form['payment_closure_date']
        remarks = request.form['remarks']
        bounce = request.form['bounce']
        bounce1 = request.form['bounce1']
        bounce2 = request.form['bounce2']
        reason_bounce = request.form['reason_bounce']

        cursor.execute('SELECT retailer_name FROM retailer_table WHERE retailer_code = %s', (retailer_code,))
        result = cursor.fetchone()

        if result and result[0] == retailer_name:
                if cheq_rcv_date and cheq_exp_date:
                    cheq_rcv_date_dt = datetime.strptime(cheq_rcv_date, '%Y-%m-%d')
                    cheq_exp_date_dt = datetime.strptime(cheq_exp_date, '%Y-%m-%d')
                    remaining_days = (cheq_exp_date_dt - cheq_rcv_date_dt).days

                else:
                    cheq_rcv_date = None
                    cheq_exp_date = None
                    remaining_days = None
                    cheque_no = None
                    bank_name = None

                remaining_amount = float(bill_amount) - (float(received_amount) + float(discount))

                query = '''UPDATE record SET bill_no=%s, bill_date=%s, retailer_code=%s, retailer_name=%s, bill_amount=%s, delivered=%s, received_amount=%s, discount=%s, remaining_amount=%s, payment_method=%s, bank_name=%s, cheque_no=%s, cheq_rcv_date=%s, cheq_exp_date=%s, remaining_days=%s, payment_closure=%s, payment_closure_date=%s, remarks=%s, bounce=%s, bounce1=%s, bounce2=%s, reason_bounce=%s 
                           WHERE id=%s'''
                values = (bill_no, bill_date, retailer_code, retailer_name, bill_amount, delivered, received_amount, discount,
                          remaining_amount, payment_method, bank_name, cheque_no, cheq_rcv_date, cheq_exp_date, remaining_days,
                          payment_closure, payment_closure_date, remarks, bounce, bounce1, bounce2, reason_bounce, record_id)
                cursor.execute(query, values)
                database1.commit()
                cursor.close()
                msg = 'Record updated successfully!'
                flash(msg)
                return redirect(url_for('view_records'))

        else:
            cursor.close()
            return "Retailer code and retailer name do not match. Please check the values."

    query = "SELECT * FROM record WHERE id = %s"
    cursor.execute(query, record_id)
    record = cursor.fetchone()
    cursor.close()
    return render_template('update_record.html', record=record)


def get_all_record():
    cursor.execute('SELECT * FROM record')
    return cursor.fetchall()


def export_to_csv(data):
    with open('record1.csv', 'w', newline="") as csvfile:

        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['id', 'bill_no', 'bill_date','retailer_code', 'retailer_name', 'bill_amount', 'delivered', 'received_amount', 'discount', 'remaining_amount',
                             'payment_method', 'bank_name', 'cheque_no', 'cheq_rcv_date', 'cheq_exp_date', 'remaining_days', 'payment_closure', 'payment_closure_date',
                             'remarks', 'bounce', 'bounce1', 'bounce2', 'reason_bounce'])

        csv_writer.writerows(data)



@app.route('/export-csv')
def export_csv():
    record1 = get_all_record()
    export_to_csv(record1)

    #df = pd.read_csv('record1.csv')
    #df.head()
    res = Response(open('record1.csv', 'r'), content_type='csv', headers={'Content-Disposition': 'attachement; filename=record1.csv'})
    return res

df = pandas.read_csv('record1.csv')
df1 = pd.DataFrame(df)
print(df1)




@app.route('/admin_register', methods=['GET', 'POST'])
@csrf.exempt
def admin_register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:

        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = database1.cursor()
        cursor.execute(
            'SELECT * FROM admin_record WHERE username = % s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account Already Exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'name must contain only characters and numbers !'
        else:
            cursor.execute('INSERT INTO admin_record VALUES \
            (NULL, % s, % s, % s)', (username, password, email))
            database1.commit()
            msg = 'You have successfully registered !'
            return render_template('login.html', msg=msg)
    elif request.method == 'POST':
           msg = 'please fill out the form !'
    return render_template('admin-register.html', msg=msg )




@app.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
        msg = ''
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM admin_record WHERE username = %s AND password = %s', (username, password,))
            account = cursor.fetchone()
            if account:
                user = User(id=account['id'], username=account['username'])
                login_user(user)
                next_page = request.args.get('next')
                if not next_page or next_page == '/login':
                    next_page = url_for('home')
                return redirect(next_page)
            else:
                msg = 'Incorrect username / password!'
        return render_template('login.html', msg=msg)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('front'))

#Reterive Dedeuplicated data and individual data


@app.route('/dedup_records')
@login_required
def dedup_records():
    records12 = get_deduplicated_records()
    return render_template('dedup_records.html', records=records12)



@app.route('/update1_bak')
@login_required
def update1_bak():
    #cursor = get_db_connection().cursor()
    cursor=database1.cursor()
    query = "SELECT * FROM record"
    cursor.execute(query)
    records = cursor.fetchall()
    cursor.close()
    print(records)  # Add this line to debug
    return render_template('update1-bak.html', records=records)


@app.route('/update_record1/<int:record_id>', methods=['POST'])
@login_required
def update_record1(record_id):
    cursor = database1.cursor()
    try:
        data = request.get_json()
        print('Received data:', data)  # Log received data

        if not data:
            return jsonify(success=False, message='No data received')

        for key in ['cheq_rcv_date', 'cheq_exp_date', 'payment_closure_date']:
            if data.get(key) == 'None':
                data[key] = None

        bill_no = data.get('bill_no')
        bill_date = data.get('bill_date')
        retailer_code = data.get('retailer_code')
        retailer_name = data.get('retailer_name')
        bill_amount = data.get('bill_amount')
        delivered = data.get('delivered')
        received_amount = data.get('received_amount')
        discount = data.get('discount')
        remaining_amount = data.get('remaining_amount')
        payment_method = data.get('payment_method')
        bank_name = data.get('bank_name')
        cheque_no = data.get('cheque_no')
        cheq_rcv_date = data.get('cheq_rcv_date')
        cheq_exp_date = data.get('cheq_exp_date')
        remaining_days = data.get('remaining_days')
        payment_closure = data.get('payment_closure')
        payment_closure_date = data.get('payment_closure_date')
        remarks = data.get('remarks')
        bounce = data.get('bounce')
        bounce1 = data.get('bounce1')
        bounce2 = data.get('bounce2')
        reason_bounce = data.get('reason_bounce')

        # Convert date strings to date objects
        if bill_date:
            bill_date = datetime.strptime(bill_date, '%Y-%m-%d').date()
        if cheq_rcv_date:
            cheq_rcv_date = datetime.strptime(cheq_rcv_date, '%Y-%m-%d').date()
        if cheq_exp_date:
            cheq_exp_date = datetime.strptime(cheq_exp_date, '%Y-%m-%d').date()
        if payment_closure_date:
            payment_closure_date = datetime.strptime(payment_closure_date, '%Y-%m-%d').date()


        cursor.execute('SELECT retailer_name FROM retailer_table WHERE retailer_code = %s', (retailer_code,))
        result = cursor.fetchone()

        if result and result[0] == retailer_name:
            if cheq_rcv_date and cheq_exp_date:
               # cheq_rcv_date_dt = datetime.datetime.strptime(cheq_rcv_date, '%Y-%m-%d')
               # cheq_exp_date_dt = datetime.datetime.strptime(cheq_exp_date, '%Y-%m-%d')
               # remaining_days = (cheq_exp_date_dt - cheq_rcv_date_dt).days
               remaining_days = (cheq_exp_date - cheq_rcv_date).days
            else:
                cheq_rcv_date = None
                cheq_exp_date = None
                remaining_days = None
                cheque_no = None
                bank_name = None

            remaining_amount = float(bill_amount) - (float(received_amount) + float(discount))

            query = '''UPDATE record SET bill_no=%s, bill_date=%s, retailer_code=%s, retailer_name=%s, bill_amount=%s, delivered=%s, received_amount=%s, discount=%s, remaining_amount=%s, payment_method=%s, bank_name=%s, cheque_no=%s, cheq_rcv_date=%s, cheq_exp_date=%s, remaining_days=%s, payment_closure=%s, payment_closure_date=%s, remarks=%s, bounce=%s, bounce1=%s, bounce2=%s, reason_bounce=%s 
                       WHERE id=%s'''
            values = (
                bill_no, bill_date, retailer_code, retailer_name, bill_amount, delivered, received_amount, discount,
                remaining_amount, payment_method, bank_name, cheque_no, cheq_rcv_date, cheq_exp_date, remaining_days,
                payment_closure, payment_closure_date, remarks, bounce, bounce1, bounce2, reason_bounce, record_id)
            cursor.execute(query, values)
            database1.commit()
            return jsonify(success=True, message='Record updated successfully')
        else:
            return jsonify(success=False, message='Retailer code and name do not match')
    except Exception as e:
        print(f'Error: {e}')  # Log the error
        return jsonify(success=False, message=f'An error occurred: {str(e)}')



@app.route('/delete_record1/<int:record_id>', methods=['POST'])
@csrf.exempt
@login_required
def delete_record1(record_id):
    cursor = database1.cursor()
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    #connection = get_db_connection()
   # cursor = connection.cursor()
    cursor.execute('SELECT * FROM admin_record WHERE username = %s AND password = %s', (username, password))
    user = cursor.fetchone()

    if user:
        cursor.execute('DELETE FROM record WHERE id = %s', (record_id,))
        #connection.commit()
        database1.commit()
        cursor.close()

        #connection.close()
        return jsonify(success=True, message="Record deleted successfully.")
    else:
        cursor.close()
        #connection.close()
        return jsonify(success=False, message="Invalid credentials.")


@app.route('/retailer_record')
@login_required
def retailer_record():
    return render_template("retailer_record.html")






db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'P@ssw0rd@123',
    'database': 'billing',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**db_config)


@app.route('/get_bill_details', methods=['GET', 'POST'])
def get_bill_details(bill_no=None):
    if not bill_no:
        bill_no = request.args.get('bill_no')
        app.logger.info(f"Received bill_no from query param: {bill_no}")

    conn = None
    cursor = None
    bill_details = None

    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT * FROM record WHERE bill_no = %s", (bill_no,))
        bill_details = cursor.fetchone()

        if bill_details:
            # Format the date fields to string in 'YYYY-MM-DD' format
            for key in bill_details:
                if isinstance(bill_details[key], datetime):
                    bill_details[key] = bill_details[key].strftime('%Y-%m-%d')

        app.logger.info(f"Fetched bill_details: {bill_details}")

    except pymysql.MySQLError as e:
        app.logger.error(f"Error fetching bill details: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return jsonify(bill_details)


@app.route('/add_record_new', methods=['POST'])
@csrf.exempt
def add_record_new():
    msg=''

    data = request.form.to_dict()
    bill_no = data.get('bill_no')
    bill_date = data.get('bill_date')
    retailer_code = data.get('retailer_code')
    retailer_name = data.get('retailer_name')
    bill_amount = data.get('bill_amount')
    delivered = data.get('delivered')
    received_amount = data.get('received_amount')
    discount = data.get('discount')
    remaining_amount = data.get('remaining_amount')
    payment_method = data.get('payment_method')
    bank_name = data.get('bank_name')
    cheque_no = data.get('cheque_no')
    cheq_rcv_date = data.get('cheq_rcv_date')
    cheq_exp_date = data.get('cheq_exp_date')
    remaining_days = data.get('remaining_days')
    payment_closure = data.get('payment_closure')
    payment_closure_date = data.get('payment_closure_date')
    remarks = data.get('remarks')
    bounce = data.get('bounce')
    bounce1 = data.get('bounce1')
    bounce2 = data.get('bounce2')
    reason_bounce = data.get('reason_bounce')

    if bill_date:
        bill_date = datetime.strptime(bill_date, '%Y-%m-%d').date()
    if cheq_rcv_date:
        cheq_rcv_date = datetime.strptime(cheq_rcv_date, '%Y-%m-%d').date()
    if cheq_exp_date:
        cheq_exp_date = datetime.strptime(cheq_exp_date, '%Y-%m-%d').date()
    if payment_closure_date:
        payment_closure_date = datetime.strptime(payment_closure_date, '%Y-%m-%d').date()


    conn = get_db_connection()
    cursor = conn.cursor()



    if cheq_rcv_date and cheq_exp_date:
        #cheq_rcv_date_dt = datetime.strptime(cheq_rcv_date, '%Y-%m-%d')
        #cheq_exp_date_dt = datetime.strptime(cheq_exp_date, '%Y-%m-%d')
        remaining_days = (cheq_exp_date - cheq_rcv_date).days

    else:
        cheq_rcv_date = None
        cheq_exp_date = None
        remaining_days = None
        cheque_no = None
        bank_name = None

    cursor.execute("""
        INSERT INTO record (bill_no, bill_date, retailer_code, retailer_name, bill_amount, delivered, 
                            received_amount, discount, remaining_amount, payment_method, bank_name, 
                            cheque_no, cheq_rcv_date, cheq_exp_date, remaining_days, payment_closure, 
                            payment_closure_date, remarks, bounce, bounce1, bounce2, reason_bounce)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (bill_no, bill_date, retailer_code, retailer_name, bill_amount, delivered, received_amount, discount,
          remaining_amount, payment_method, bank_name, cheque_no, cheq_rcv_date, cheq_exp_date, remaining_days,
          payment_closure, payment_closure_date, remarks, bounce, bounce1, bounce2, reason_bounce))
    conn.commit()
    conn.close()
    flash('Record added successfully!')
    return redirect(url_for('record_update', msg=msg))

@app.route('/update_record_new', methods=['POST'])
@csrf.exempt
def update_record_new():
    msg=''
    data = request.form.to_dict()
    record_id = data.get('record_id')
    bill_no = data.get('bill_no')
    bill_date = data.get('bill_date')
    retailer_code = data.get('retailer_code')
    retailer_name = data.get('retailer_name')
    bill_amount = data.get('bill_amount')
    delivered = data.get('delivered')
    received_amount = data.get('received_amount')
    discount = data.get('discount')
    remaining_amount = data.get('remaining_amount')
    payment_method = data.get('payment_method')
    bank_name = data.get('bank_name')
    cheque_no = data.get('cheque_no')
    cheq_rcv_date = data.get('cheq_rcv_date')
    cheq_exp_date = data.get('cheq_exp_date')
    remaining_days = data.get('remaining_days')
    payment_closure = data.get('payment_closure')
    payment_closure_date = data.get('payment_closure_date')
    remarks = data.get('remarks')
    bounce = data.get('bounce')
    bounce1 = data.get('bounce1')
    bounce2 = data.get('bounce2')
    reason_bounce = data.get('reason_bounce')



    conn = get_db_connection()
    cursor = conn.cursor()


    if bill_date:
        bill_date = datetime.strptime(bill_date, '%Y-%m-%d').date()
    if cheq_rcv_date:
        cheq_rcv_date = datetime.strptime(cheq_rcv_date, '%Y-%m-%d').date()
    if cheq_exp_date:
        cheq_exp_date = datetime.strptime(cheq_exp_date, '%Y-%m-%d').date()
    if payment_closure_date:
        payment_closure_date = datetime.strptime(payment_closure_date, '%Y-%m-%d').date()



    if cheq_rcv_date and cheq_exp_date:
        #cheq_rcv_date_dt = datetime.strptime(cheq_rcv_date, '%Y-%m-%d')
        #cheq_exp_date_dt = datetime.strptime(cheq_exp_date, '%Y-%m-%d')
        remaining_days = (cheq_exp_date - cheq_rcv_date).days

    else:
        cheq_rcv_date = None
        cheq_exp_date = None
        remaining_days = None
        cheque_no = None
        bank_name = None

    cursor.execute("""
        UPDATE record
        SET bill_no=%s, bill_date=%s, retailer_code=%s, retailer_name=%s, bill_amount=%s, delivered=%s, 
            received_amount=%s, discount=%s, remaining_amount=%s, payment_method=%s, bank_name=%s, 
            cheque_no=%s, cheq_rcv_date=%s, cheq_exp_date=%s, remaining_days=%s, payment_closure=%s, 
            payment_closure_date=%s, remarks=%s, bounce=%s, bounce1=%s, bounce2=%s, reason_bounce=%s
        WHERE id=%s
    """, (bill_no, bill_date, retailer_code, retailer_name, bill_amount, delivered, received_amount, discount,
          remaining_amount, payment_method, bank_name, cheque_no, cheq_rcv_date, cheq_exp_date, remaining_days,
          payment_closure, payment_closure_date, remarks, bounce, bounce1, bounce2, reason_bounce, record_id))
    conn.commit()
    conn.close()
    flash('Record updated successfully!')
    return redirect(url_for('record_update', msg=msg))


'''
@app.route('/record_new')
def record_new():
    return render_template('record-update.html', record=None)
'''
@app.route('/record_update')
@csrf.exempt
def record_update():
    return render_template('record-update.html')



if __name__ == "__main__":
    app.run(host = "192.168.180.15", debug = True, port = int("6009"))


