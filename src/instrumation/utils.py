import csv
import os
from datetime import datetime

class TestLogger:
    def __init__(self, filename="test_report.csv"):
        self.filename = filename
        if not os.path.exists(self.filename):
            self._write_header()

    def _write_header(self):
        with open(self.filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Test Name", "Data", "Result"])

    def log(self, test_name, data, result):
        with open(self.filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), test_name, data, result])
        print(f"Logged: {test_name} -> {result}")
