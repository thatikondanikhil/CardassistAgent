import sqlite3
from contextlib import closing


class BankDatabase:
    def __init__(self, db_name="bank.db"):
        self.db_name = db_name
    

    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def create_tables(self):
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                CREATE TABLE customers (
                    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    phone VARCHAR(10),
                    password TEXT NOT NULL,
                    address TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """)
                cursor.execute("""
                CREATE TABLE cards (
                    card_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    card_type VARCHAR NOT NULL CHECK(card_type IN ('debit', 'credit')),
                    card_number VARCHAR(9) NOT NULL UNIQUE,
                    expiry_date VARCHAR(5) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
                );
                """)
                cursor.execute("""
                CREATE TABLE messages (
                message_id VARCHAR(36) PRIMARY KEY,              
                session_id VARCHAR(36) NOT NULL,               
                customer_id INTEGER NOT NULL,                    
                role VARCHAR(10) CHECK(role IN ('user', 'assistant')) NOT NULL,
                content VARCHAR(10000) NOT NULL,                 
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
                
                );""")
                
              
                conn.commit()
        except Exception as e:
            return None





if __name__ == "__main__":
    db = BankDatabase()
    db.create_tables()
