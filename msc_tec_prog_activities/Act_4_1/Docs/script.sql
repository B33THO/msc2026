DROP DATABASE IF EXISTS BankAccounts;
CREATE DATABASE IF NOT EXISTS BankAccounts;
USE BankAccounts;

DROP TABLE IF EXISTS  client;
CREATE TABLE client (
    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    paternal_surname VARCHAR(100) NOT NULL,
    maternal_surname VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL
) AUTO_INCREMENT = 1000;

DROP TABLE IF EXISTS  account;
CREATE TABLE account (
    account_number INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    id_client INT NOT NULL,
    balance DECIMAL(10,2) NOT NULL,
    created_at DATE NOT NULL,

    CONSTRAINT chk_positive_c_balance CHECK (balance >= 0),
    CONSTRAINT fk_client FOREIGN KEY (id_client) REFERENCES client(id) ON DELETE CASCADE

)AUTO_INCREMENT = 1000;

DROP TABLE IF EXISTS  credit_account;
CREATE TABLE credit_account (
    account_number INT NOT NULL PRIMARY KEY,
    credit_limit DECIMAL(10,2) NOT NULL,
    debt DECIMAL(10,2) NOT NULL DEFAULT 0,
    CONSTRAINT chk_credit_limit CHECK (credit_limit >= 0),
    CONSTRAINT chk_credit_debt CHECK (debt >= 0 AND debt <= credit_limit),
    CONSTRAINT fk_credit_account FOREIGN KEY (account_number)
        REFERENCES account(account_number) ON DELETE CASCADE
);

