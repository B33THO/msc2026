DROP DATABASE IF EXISTS BankAccounts;
CREATE DATABASE IF NOT EXISTS BankAccounts;
USE BankAccounts;

DROP TABLE IF EXISTS  client;
CREATE TABLE client (
    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    PaternalSurname VARCHAR(100) NOT NULL,
    MaternalSurname VARCHAR(100) NOT NULL,
    Name VARCHAR(100) NOT NULL
) AUTO_INCREMENT = 1000;

DROP TABLE IF EXISTS  account;
CREATE TABLE account (
    accountNumber INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    idClient INT NOT NULL,
    balance DECIMAL(10,2) NOT NULL,
    createdAt DATE NOT NULL,

    CONSTRAINT chk_positive_c_balance CHECK (balance >= 0),
    CONSTRAINT fk_client FOREIGN KEY (idClient) REFERENCES client(Id) ON DELETE CASCADE

)AUTO_INCREMENT = 1000;

DROP TABLE IF EXISTS  creditAccount;
CREATE TABLE creditAccount (
    accountNumber INT NOT NULL PRIMARY KEY,
    creditLimit DECIMAL(10,2) NOT NULL,
    debt DECIMAL(10,2) NOT NULL DEFAULT 0,
    CONSTRAINT chk_credit_limit CHECK (creditLimit >= 0),
    CONSTRAINT chk_credit_debt CHECK (debt >= 0 AND debt <= creditLimit),
    CONSTRAINT fk_credit_account FOREIGN KEY (accountNumber)
        REFERENCES account(accountNumber) ON DELETE CASCADE
);

