import os
import pandas as pd
import pymysql
from flask import request, redirect, url_for, flash, render_template
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_file(file_path):
    database1 = pymysql.connect(host="localhost", user="root", passwd="P@ssw0rd@123", db="billing")

    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    elif file_ext == '.csv':
        df = pd.read_csv(file_path)

    cursor = database1.cursor()

    for index, row in df.iterrows():
        bill_no = row['bill_no']
        retailer_code = row['retailer_code']
        retailer_name = row['retailer_name']

        query_check = '''
            SELECT COUNT(*) FROM record
            WHERE bill_no = %s AND retailer_code = %s AND retailer_name = %s
        '''
        cursor.execute(query_check, (bill_no, retailer_code, retailer_name))
        count = cursor.fetchone()[0]

        if count == 0:
            query_insert = '''
                INSERT INTO record (bill_no, bill_date, retailer_code, retailer_name, bill_amount, delivered, received_amount, discount, remaining_amount,
                                    payment_method, bank_name, cheque_no, cheq_rcv_date, cheq_exp_date, remaining_days, payment_closure, payment_closure_date,
                                    remarks, bounce, bounce1, bounce2, reason_bounce)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(query_insert, (
                row['bill_no'], row['bill_date'], row['retailer_code'], row['retailer_name'], row['bill_amount'],
                row['delivered'], row['received_amount'],
                row['discount'], row['remaining_amount'], row['payment_method'], row['bank_name'], row['cheque_no'],
                row['cheq_rcv_date'],
                row['cheq_exp_date'], row['remaining_days'], row['payment_closure'], row['payment_closure_date'],
                row['remarks'], row['bounce'],
                row['bounce1'], row['bounce2'], row['reason_bounce']
            ))
            database1.commit()

def upload_files():
    if request.method == 'POST':
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            flash('No files selected')
            return redirect(request.url)

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                process_file(file_path)

        flash('Files successfully uploaded and processed')
        return redirect(url_for('upload_files_route'))

    return render_template('upload.html')
