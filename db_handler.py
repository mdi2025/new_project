#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import MySQLdb
import MySQLdb.cursors
import sys

class DBHandler:
    def __init__(self):
        self.host = "db.dev.erp.mdi"
        self.user = "erp"
        self.password = "erpdeveloper"
        self.dbname = "mdiacc"
        self.conn = None

    def get_connection(self):
        """Returns a database connection."""
        try:
            if self.conn is None or not self.conn.open:
                self.conn = MySQLdb.connect(
                    host=self.host,
                    user=self.user,
                    passwd=self.password,
                    db=self.dbname,
                    charset='utf8',
                    cursorclass=MySQLdb.cursors.DictCursor
                )
            return self.conn
        except MySQLdb.Error as e:
            print("Error connecting to MySQL Database: {}".format(e))
            return None

    def fetch_all(self, query, params=None):
        """Executes a query and returns all results."""
        conn = self.get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except MySQLdb.Error as e:
            print("Error executing query: {}".format(e))
            return []
        finally:
            cursor.close()

    def execute_query(self, query, params=None):
        """Executes a query (INSERT, UPDATE, DELETE)."""
        conn = self.get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return True
        except MySQLdb.Error as e:
            print("Error executing query: {}".format(e))
            conn.rollback()
            return False
        finally:
            cursor.close()

    def close(self):
        """Closes the connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

# Global instance for easy access
db = DBHandler()
