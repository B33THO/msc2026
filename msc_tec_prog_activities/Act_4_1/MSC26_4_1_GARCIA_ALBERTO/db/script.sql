DROP DATABASE IF EXISTS BankAccounts;
CREATE DATABASE IF NOT EXISTS BankAccounts;
USE BankAccounts;

DROP TABLE IF EXISTS  Client;
CREATE TABLE Client (
    Id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    PaternalSurname VARCHAR(100) NOT NULL,
    MaternalSurname VARCHAR(100) NOT NULL,
    Name VARCHAR(100) NOT NULL
) AUTO_INCREMENT = 1000;

DROP TABLE IF EXISTS  Account;
CREATE TABLE Account (
    AccountNumber INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    IdClient INT NOT NULL,
    Balance DECIMAL(10,2) NOT NULL,
    CreatedAt DATE NOT NULL,

    CONSTRAINT chk_positive_c_balance CHECK (Balance >= 0),
    CONSTRAINT fk_client FOREIGN KEY (IdClient) REFERENCES Client(Id) ON DELETE CASCADE

)AUTO_INCREMENT = 1000;

DROP TABLE IF EXISTS  CreditAccount;
CREATE TABLE CreditAccount (
    AccountNumber INT NOT NULL PRIMARY KEY,
    CreditLimit DECIMAL(10,2) NOT NULL,
    Debt DECIMAL(10,2) NOT NULL DEFAULT 0,
    CONSTRAINT chk_credit_limit CHECK (CreditLimit >= 0),
    CONSTRAINT chk_credit_debt CHECK (Debt >= 0 AND Debt <= CreditLimit),
    CONSTRAINT fk_credit_account FOREIGN KEY (AccountNumber)
        REFERENCES Account(AccountNumber) ON DELETE CASCADE
);

