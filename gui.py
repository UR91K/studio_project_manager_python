"""
A GUI Application for Ableton Live Set Management

This module provides a GUI application using PyQt5 to allow users to perform a full-text search on
Ableton Live Set projects stored in a SQLite database. Search results include key project details such 
as name, creator, key, tempo, time signature, estimated duration, furthest bar, plugins used, and sample paths.

The app provides a search bar at the top where users can enter their query. Search results are displayed 
in a table format with columns representing different attributes of the Ableton Live Set project.

Attributes:
    DATABASE_PATH (Path): Path to the SQLite database file.
    columns_info_dict (dict): Dictionary containing column names and their corresponding indexes.
    excluded_columns (list): List of column names to be excluded from the display.

Functions:
    perform_full_text_search(query): Executes a full-text search on the SQLite database using the provided query 
                                     and returns the results.

Classes:
    SearchApp(QMainWindow): Main GUI class responsible for displaying the search bar, handling input,
                            and displaying search results.

Note:
    This module initializes the SQLite database with the required tables and columns if they do not exist 
    and loads necessary configurations from a "config.toml" file. The app currently focuses on GUI and search 
    functionalities, with plans for additional features and improvements in the future.
"""

import os
import sqlite3
from pathlib import Path
from fuzzywuzzy import fuzz
import toml
from PyQt5.QtWidgets import (
    QApplication,
    QLineEdit,
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
config = toml.load("config.toml")
user_home_dir = os.path.expanduser("~")
DATABASE_PATH = Path(config["database_path"]["path"].replace("{USER_HOME}", user_home_dir))
print("Database path: ", DATABASE_PATH)

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(ableton_live_sets)")
columns_info = cursor.fetchall()
conn.close()

def get_best_match_score(row, query, exclude_columns):
    best_score = 0
    for index, column_info in enumerate(columns_info):
        column_name = column_info[1]
        if column_name not in exclude_columns and row[index] is not None:
            score = fuzz.ratio(str(row[index]).lower(), query.lower())
            best_score = max(best_score, score)
    return best_score

def perform_fuzzy_search(query):
    exclude_columns = ["uuid", "identifier", "xml_root", "path", "file_hash", "last_scan_timestamp"]
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM ableton_live_sets")
    all_rows = cursor.fetchall()

    match_scores = [(row, get_best_match_score(row, query, exclude_columns)) for row in all_rows]

    sorted_matches = sorted(match_scores, key=lambda x: x[1], reverse=True)

    top_matches = sorted_matches[:10]

    conn.close()

    return top_matches

class SearchApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SQLite Search GUI")
        
        self.headers = [info[1] for info in columns_info if info[1] not in ["uuid", 
                                                                            "identifier", 
                                                                            "xml_root", "path", 
                                                                            "file_hash", 
                                                                            "last_scan_timestamp"]]

        self.search_line_edit = QLineEdit(self)
        self.result_table = QTableWidget(self)
        self.result_table.setColumnCount(len(columns_info) - len(["uuid", 
                                                                  "identifier", 
                                                                  "xml_root", 
                                                                  "path", 
                                                                  "file_hash", 
                                                                  "last_scan_timestamp"]))
        self.result_table.setHorizontalHeaderLabels(self.headers)

        layout = QVBoxLayout()
        layout.addWidget(self.search_line_edit)
        layout.addWidget(self.result_table)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.search_line_edit.textChanged.connect(self.perform_search)

    def perform_search(self):
        query = self.search_line_edit.text()
        
        if not query:
            self.result_table.setRowCount(0)
            return
        
        matches = perform_fuzzy_search(query)
        
        self.result_table.setRowCount(len(matches))
        for row, (match_row, score) in enumerate(matches):
            for col_index, value in enumerate(match_row):
                column_name = columns_info[col_index][1]
                if column_name not in ["uuid", 
                                       "identifier", 
                                       "xml_root", 
                                       "path", 
                                       "file_hash", 
                                       "last_scan_timestamp"
                                       ]:
                    self.result_table.setItem(row, self.headers.index(column_name), QTableWidgetItem(str(value)))

if __name__ == "__main__":
    app = QApplication([])
    window = SearchApp()
    window.show()
    app.exec_()