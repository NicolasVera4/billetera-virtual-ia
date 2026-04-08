CREATE DATABASE enterprise_finance_ai;
\c enterprise_finance_ai;

CREATE TYPE transaction_type AS ENUM ('income', 'expense');

CREATE TYPE document_type AS ENUM ('invoice', 'receipt', 'statement', 'other');

CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(id),
    category_id INT REFERENCES categories(id),
    transaction_date DATE NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    type transaction_type NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_category ON transactions(category_id);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(id),
    document_type document_type NOT NULL,
    provider TEXT,
    document_date DATE,
    total_amount NUMERIC(14,2),
    currency VARCHAR(10) DEFAULT 'USD',
    file_path TEXT NOT NULL,
    extracted_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_date ON documents(document_date);
CREATE INDEX idx_documents_provider ON documents(provider);

CREATE TABLE document_transactions (
    document_id INT REFERENCES documents(id) ON DELETE CASCADE,
    transaction_id INT REFERENCES transactions(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, transaction_id)
);

CREATE TABLE anomaly_flags (
    id SERIAL PRIMARY KEY,
    transaction_id INT REFERENCES transactions(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO sources (name, description)
VALUES
    ('manual_upload', 'Manual dataset upload'),
    ('documents', 'Invoices and receipts ingestion');

INSERT INTO categories (name, description)
VALUES
    ('Supermarket', 'Groceries and food'),
    ('Utilities', 'Electricity, water, gas'),
    ('Rent', 'Office or property rent'),
    ('Salary', 'Employee salaries'),
    ('Other', 'Uncategorized expenses');
