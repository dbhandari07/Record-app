import pandas
import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from db import insert_chq_payment, add_record, get_deduplicated_records, get_db_connection, process_excel_file
from openpyxl.utils import datetime
from werkzeug.utils import secure_filename
import os
import MySQLdb.cursors
import pandas as pd
from datetime import datetime
import csv
from file_upload import allowed_file, process_file, upload_files
from flask import request, jsonify
import re
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user




app = Flask(__name__)
app.secret_key = 'supersecretkey'


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
    connection = get_db_connection()
    cursor = connection.cursor()
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

def home():
    return render_template("home.html")



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
def upload_files_route():
    return upload_files()



# load to DB


@app.route('/record', methods=['GET', 'POST'])

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
def view_records():
    cursor = database1.cursor()
    query = "SELECT * FROM record"
    cursor.execute(query)
    records = cursor.fetchall()
    cursor.close()
    print(records)  # Add this line to debug
    return render_template('view_records.html', records=records)



@app.route('/delete_record/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    cursor = database1.cursor()
    query = "DELETE FROM record WHERE id = %s"
    cursor.execute(query, (record_id,))
    database1.commit()
    cursor.close()
    flash('Record deleted successfully!')
    return redirect(url_for('view_records'))


@app.route('/update_record/<int:record_id>', methods=['GET', 'POST'])

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

def login():


    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = database1.cursor()

        cursor.execute('SELECT * FROM admin_record WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            msg = 'Logged in Successfully !'
            return render_template('home.html', msg=msg)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg=msg)


@app.route('/logout')

def logout():

    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('front'))


#Reterive Dedeuplicated data and individual data


@app.route('/dedup_records')

def dedup_records():
    records12 = get_deduplicated_records()
    return render_template('dedup_records.html', records=records12)



@app.route('/update1_bak')
def update1_bak():
    cursor = database1.cursor()
    query = "SELECT * FROM record"
    cursor.execute(query)
    records = cursor.fetchall()
    cursor.close()
    print(records)  # Add this line to debug
    return render_template('update1-bak.html', records=records)


@app.route('/update_record1/<int:record_id>', methods=['POST'])
def update_record1(record_id):
    database1 = pymysql.connect(host="localhost", user="root", passwd="P@ssw0rd@123", db="billing")
    data = request.json
    cursor = database1.cursor()
    update_fields = []
    update_values = []

    for field, value in data.items():
        update_fields.append(f"{field} = %s")
        update_values.append(value)

    update_values.append(record_id)

    query_update = f'''
        UPDATE record
        SET {', '.join(update_fields)}
        WHERE id = %s
    '''
    try:
        cursor.execute(query_update, update_values)
        database1.commit()
        print(f"Updated record ID {record_id} with data: {data}")  # Debugging information
        return jsonify({'status': 'success', 'message': 'Record updated successfully!'})
    except Exception as e:
        print(f"Error updating record ID {record_id}: {e}")  # Debugging information
        return jsonify({'status': 'error', 'message': 'Error updating record.'})




if __name__ == "__main__":
    app.run(host = "192.168.180.15", debug = True, port = int("6009"))


