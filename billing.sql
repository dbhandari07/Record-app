CREATE DATABASE IF NOT EXISTS billing DEFAULT CHARACTER SET utf16 COLLATE utf16_general_ci;
USE billing;
create table cheque_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATETIME NOT NULL,
    amount FLOAT NOT NULL,
    payer_name VARCHAR(255) NOT NULL);
    

create table cash_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATETIME NOT NULL,
    amount FLOAT NOT NULL,
    received_from VARCHAR(255) NOT NULL
);


create table due_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATETIME NOT NULL,
    amount FLOAT NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    due_date  DATETIME 
);

