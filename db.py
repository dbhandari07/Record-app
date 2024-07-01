import pandas as pd
from flask import Flask, render_template, request, redirect, session, jsonify, flash, url_for
import pymysql
import xlrd
from flask_mysqldb import MySQL
import MySQLdb.cursors
import os
import numpy as np


app = Flask(__name__)
#from flask_socketio import emit
#from app import socketio  # Assuming 'app' is your Flask app instance

def insert_chq_payment(filename):

        chq_data = pd.read_excel(filename)
        #print (chq_data.head())

        #sheet = chq_data.sheet_by_name("source")

        database = MySQLdb.connect(host="localhost", user="root", passwd="P@ssw0rd@123", db="billing")

        cursor = database.cursor()

        query = """INSERT INTO cheque_payments(date, amount, payer_name) VALUES(%s, %s, %s)"""

        for index, row in chq_data.iterrows():
            date = row['date']
            amount = row['amount']
            payer_name = row['payer_name']
            values = (date, amount, payer_name)
            cursor.execute(query, values)



        cursor.close()
        database.commit()

        print("")
        print ("All Done !!!")


def add_record():
   # add_data = pd.read_excel(filename)
    # print (chq_data.head())

    # sheet = chq_data.sheet_by_name("source")

    database = MySQLdb.connect(host="localhost", user="root", passwd="P@ssw0rd@123", db="billing")

    cursor = database.cursor()


    query = '''INSERT INTO record (bill_no, bill_date, retailer_code, retailer_name, bill_amount, delivered, received_amount, discount, remaining_amount, payment_method, bank_name, cheqque_no, cheq_rcv_date, cheq_exp_date, remaining_days, payment_closure, payment_closure_date, remarks, bounce, bounce1, bounce2, bounce_reason) 
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
    cursor.execute(query)

    cursor.close()
    database.commit()

    print("")
    print("All Done !!!")



# You can define more functions related to database operations if needed

def get_db_connection():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='P@ssw0rd@123',
        db='billing',
        cursorclass=pymysql.cursors.DictCursor  # Use DictCursor to fetch rows as dictionaries
    )
    return connection


def get_deduplicated_records():
    connection = get_db_connection()
    cursor = connection.cursor()

    query = '''
        SELECT retailer_name, retailer_code,
               SUM(bill_amount) AS total_bill_amount,
               MAX(bill_date) AS last_bill_date
        FROM record
        GROUP BY retailer_name, retailer_code
        ORDER BY retailer_name, retailer_code
    '''
    cursor.execute(query)
    deduplicated_records = cursor.fetchall()

    consolidated_records = []
    for record in deduplicated_records:

        retailer_name = record['retailer_name']
        retailer_code = record['retailer_code']
        total_bill_amount = record['total_bill_amount']
        last_bill_date = record['last_bill_date']

        # Query individual records for each retailer_name and retailer_code
        query_individual = '''
            SELECT * FROM record
            WHERE retailer_name = %s AND retailer_code = %s
            ORDER BY bill_date DESC
        '''
        cursor.execute(query_individual, (retailer_name, retailer_code))
        individual_records = cursor.fetchall()

        consolidated_records.append({

            'retailer_name': retailer_name,
            'retailer_code': retailer_code,
            'total_bill_amount': total_bill_amount,
            'last_bill_date': last_bill_date,
            'individual_records': individual_records
        })

    connection.close()
    return consolidated_records




# new upload file
def process_excel_file(file_path):
        database = MySQLdb.connect(host="localhost", user="root", passwd="P@ssw0rd@123", db="billing")

        cursor = database.cursor()
        df = pd.read_excel(file_path)
        df = df.replace({np.nan: None})
        print("NaN count per column after replacement:\n", df.isnull().sum())
        print("Columns in DataFrame:", df.columns)
        print("First few rows of DataFrame:\n", df.head())

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
                    row['cheq_exp_date'], row['remaining_days'], row['payment_closure'],
                    row['payment_closure_date'], row['remarks'], row['bounce'],
                    row['bounce1'], row['bounce2'], row['reason_bounce']
                ))
                database.commit()
        print("")
        print("All Done !!!")






if __name__ == '__main__':
    app.run(debug=True)  # No app.run() here; this block will not execute when imported