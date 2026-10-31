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
    CONSTRAINT uq_client UNIQUE (id_client), -- Cada cliente tiene una sola cuenta
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


-- ---------------------------------------------------------------------------------
-- DATOS INICIALES
-- Los ids de client y los números de cuenta empiezan en 1000 por el AUTO_INCREMENT,
-- así que el cliente 1000 tiene la cuenta 1000, el 1001 la 1001, etc.
-- ---------------------------------------------------------------------------------
INSERT INTO client (paternal_surname, maternal_surname, name) VALUES
    ('BRITO', 'DELGADO', 'ALAN'),          -- 1000
    ('QUITO', 'MADERA', 'ESTEBAN'),        -- 1001
    ('VACA', 'DEL CORRAL', 'ZOILA'),       -- 1002
    ('GALINDO', 'SEGÚN', 'MÓNICA'),        -- 1003
    ('TILLA', 'DE PATATA', 'AITOR'),       -- 1004
    ('BRONCA', 'SEGURA', 'ARMANDO'),       -- 1005
    ('MENTO', 'MUCHO', 'LOLA'),            -- 1006
    ('ORIA', 'BUENA', 'SUSANA'),           -- 1007
    ('PATO', 'ROJO', 'ELSA'),              -- 1008
    ('LISA', 'CRUZ', 'ANA');               -- 1009

-- Cuentas de débito (1000 - 1004) y cuentas base de las de crédito (1005 - 1009)
INSERT INTO account (id_client, balance, created_at) VALUES
    (1000, 15000.00, '2025-01-15'),
    (1001,   850.50, '2025-03-02'),
    (1002, 42000.00, '2024-11-20'),
    (1003,     0.00, '2025-06-10'),
    (1004,  3200.75, '2025-08-01'),
    (1005,  5000.00, '2024-09-12'),
    (1006,     0.00, '2025-02-14'),
    (1007, 12500.00, '2025-04-18'),
    (1008,   300.00, '2025-07-08'),
    (1009,  7800.00, '2025-10-01');

-- Datos de crédito (debt <= credit_limit por el CHECK)
INSERT INTO credit_account (account_number, credit_limit, debt) VALUES
    (1005, 20000.00,     0.00),
    (1006, 10000.00,  4500.00),
    (1007, 50000.00, 12000.00),
    (1008,  5000.00,  5000.00),
    (1009, 15000.00,  2500.00);
