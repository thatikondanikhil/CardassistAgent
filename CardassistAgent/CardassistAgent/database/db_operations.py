import sqlite3
from contextlib import closing
#from engine.generate_log import #logger

class DatabaseOps:
    def __init__(self, db_name="bank.db"):
        self.db_name = db_name

    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        return conn
    
    def insert_data(self, table, data):
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?" for _ in data.keys()])
                query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                params = list(data.values())
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            #logger.exception(f"An error occurred: {e}")
            return None


    def get_data(self, query, params=None):
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                if params is None:
                    cursor.execute(query)
                else:
                    cursor.execute(query, params)
                rows = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                result = [dict(zip(column_names, row)) for row in rows]
                return True,result
        except Exception as e:
            #logger(f"An error occurred: {e}")
            return None

    def update_data(self, table, data, condition):
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
                condition_clause = " AND ".join([f"{key} = ?" for key in condition.keys()])
                query = f"UPDATE {table} SET {set_clause} WHERE {condition_clause}"
                params = list(data.values()) + list(condition.values())
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            #logger.exception(f"An error occurred: {e}")
            return None


