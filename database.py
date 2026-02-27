import sqlite3
import datetime

class Database:
    def __init__(self, db_name="coaching_center.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        # Enable foreign key support
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # 1. Students Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unique_student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                father_name TEXT,
                mother_name TEXT,
                father_mobile TEXT,
                alternative_mobile TEXT,
                current_class TEXT NOT NULL,
                section TEXT,
                status TEXT DEFAULT 'active'
            )
        """)

        # 2. Classes Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Classes (
                class_id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT UNIQUE NOT NULL,
                monthly_fee REAL NOT NULL DEFAULT 0.0
            )
        """)

        # 3. Exams Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Exams (
                exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT NOT NULL,
                exam_name TEXT NOT NULL,
                total_marks REAL NOT NULL,
                exam_date TEXT NOT NULL
            )
        """)

        # 4. Marks Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Marks (
                mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_unique_id TEXT NOT NULL,
                exam_id INTEGER NOT NULL,
                obtained_marks REAL NOT NULL,
                FOREIGN KEY(student_unique_id) REFERENCES Students(unique_student_id) ON DELETE CASCADE,
                FOREIGN KEY(exam_id) REFERENCES Exams(exam_id) ON DELETE CASCADE
            )
        """)

        # 5. Payments Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_unique_id TEXT NOT NULL,
                class_name TEXT NOT NULL,
                month TEXT NOT NULL,
                year TEXT NOT NULL,
                amount REAL NOT NULL,
                paid_status TEXT DEFAULT 'unpaid',
                FOREIGN KEY(student_unique_id) REFERENCES Students(unique_student_id) ON DELETE CASCADE
            )
        """)

        # 6. PromotionHistory Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS PromotionHistory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_unique_id TEXT,
                year TEXT,
                from_class TEXT,
                to_class TEXT,
                overall_result_summary TEXT,
                FOREIGN KEY (student_unique_id) REFERENCES Students(unique_student_id) ON DELETE CASCADE
            )
        ''')
        
        # 7. AppConfig Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS AppConfig (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        self.conn.commit()
        self._seed_default_classes()
        self._seed_default_admin()

    def _seed_default_classes(self):
        self.cursor.execute("SELECT COUNT(*) FROM Classes")
        if self.cursor.fetchone()[0] == 0:
            default_classes = [
                ("Class 3", 500.0), ("Class 4", 500.0), ("Class 5", 500.0),
                ("Class 6", 500.0), ("Class 7", 500.0), ("Class 8", 500.0),
                ("Class 9", 500.0), ("Class 10", 500.0)
            ]
            self.cursor.executemany("INSERT INTO Classes (class_name, monthly_fee) VALUES (?, ?)", default_classes)
            self.conn.commit()

    def _seed_default_admin(self):
        self.cursor.execute("SELECT * FROM AppConfig WHERE key = 'admin_password'")
        if not self.cursor.fetchone():
            self.cursor.execute("INSERT INTO AppConfig (key, value) VALUES ('admin_password', 'admin')")
            self.conn.commit()

    def verify_admin(self, password):
        self.cursor.execute("SELECT value FROM AppConfig WHERE key = 'admin_password'")
        row = self.cursor.fetchone()
        return row and row[0] == password

    def update_admin_password(self, new_password):
        self.cursor.execute("UPDATE AppConfig SET value = ? WHERE key = 'admin_password'", (new_password,))
        self.conn.commit()

    # --- Student Operations ---
    def generate_student_id(self):
        self.cursor.execute("SELECT id FROM Students ORDER BY id DESC LIMIT 1")
        result = self.cursor.fetchone()
        next_id = 1 if result is None else result[0] + 1
        return f"STU{next_id:04d}"

    def add_student(self, name, father_name, mother_name, father_mobile, alternative_mobile, current_class, section):
        student_id = self.generate_student_id()
        self.cursor.execute("""
            INSERT INTO Students (unique_student_id, name, father_name, mother_name, father_mobile, alternative_mobile, current_class, section)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, name, father_name, mother_name, father_mobile, alternative_mobile, current_class, section))
        self.conn.commit()
        return student_id

    def get_students_by_class(self, class_name):
        self.cursor.execute("SELECT * FROM Students WHERE current_class = ? AND status = 'active'", (class_name,))
        return self.cursor.fetchall()

    def get_student_by_id(self, student_unique_id):
        self.cursor.execute("SELECT * FROM Students WHERE unique_student_id = ?", (student_unique_id,))
        return self.cursor.fetchone()

    def update_student(self, student_unique_id, name, father_name, mother_name, father_mobile, alternative_mobile, current_class, section):
        self.cursor.execute("""
            UPDATE Students 
            SET name=?, father_name=?, mother_name=?, father_mobile=?, alternative_mobile=?, current_class=?, section=?
            WHERE unique_student_id=?
        """, (name, father_name, mother_name, father_mobile, alternative_mobile, current_class, section, student_unique_id))
        self.conn.commit()

    def delete_student(self, student_unique_id):
        self.cursor.execute("DELETE FROM Students WHERE unique_student_id = ?", (student_unique_id,))
        self.conn.commit()

    # --- Class Operations ---
    def get_classes(self):
        self.cursor.execute("SELECT * FROM Classes")
        return self.cursor.fetchall()

    def get_class_fee(self, class_name):
        self.cursor.execute("SELECT monthly_fee FROM Classes WHERE class_name = ?", (class_name,))
        result = self.cursor.fetchone()
        return result[0] if result else 0.0

    def update_class_fee(self, class_name, fee):
        self.cursor.execute("UPDATE Classes SET monthly_fee = ? WHERE class_name = ?", (fee, class_name))
        self.conn.commit()

    # --- Exam Operations ---
    def add_exam(self, class_name, exam_name, total_marks, exam_date):
        self.cursor.execute("""
            INSERT INTO Exams (class_name, exam_name, total_marks, exam_date)
            VALUES (?, ?, ?, ?)
        """, (class_name, exam_name, total_marks, exam_date))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_exams_by_class(self, class_name):
        self.cursor.execute("SELECT * FROM Exams WHERE class_name = ?", (class_name,))
        return self.cursor.fetchall()

    def delete_exam(self, exam_id):
        self.cursor.execute("DELETE FROM Exams WHERE exam_id = ?", (exam_id,))
        self.conn.commit()

    # --- Marks Operations ---
    def add_or_update_mark(self, student_unique_id, exam_id, obtained_marks):
        # Check if exists
        self.cursor.execute("SELECT mark_id FROM Marks WHERE student_unique_id = ? AND exam_id = ?", (student_unique_id, exam_id))
        result = self.cursor.fetchone()
        if result:
            self.cursor.execute("UPDATE Marks SET obtained_marks = ? WHERE mark_id = ?", (obtained_marks, result[0]))
        else:
            self.cursor.execute("INSERT INTO Marks (student_unique_id, exam_id, obtained_marks) VALUES (?, ?, ?)", 
                                (student_unique_id, exam_id, obtained_marks))
        self.conn.commit()

    def get_marks_for_student(self, student_unique_id):
        self.cursor.execute("""
            SELECT e.exam_name, e.total_marks, m.obtained_marks, e.exam_date, e.class_name
            FROM Marks m
            JOIN Exams e ON m.exam_id = e.exam_id
            WHERE m.student_unique_id = ?
        """, (student_unique_id,))
        return self.cursor.fetchall()

    def get_marks_by_exam(self, exam_id):
        self.cursor.execute("""
            SELECT s.unique_student_id, s.name, m.obtained_marks 
            FROM Students s
            LEFT JOIN Marks m ON s.unique_student_id = m.student_unique_id AND m.exam_id = ?
            WHERE s.current_class = (SELECT class_name FROM Exams WHERE exam_id = ?)
            AND s.status = 'active'
        """, (exam_id, exam_id))
        return self.cursor.fetchall()

    def get_highest_marks_for_exam(self, exam_id):
        self.cursor.execute("SELECT MAX(obtained_marks) FROM Marks WHERE exam_id = ?", (exam_id,))
        res = self.cursor.fetchone()
        return res[0] if res and res[0] is not None else 0

    def get_average_marks_for_exam(self, exam_id):
        self.cursor.execute("SELECT AVG(obtained_marks) FROM Marks WHERE exam_id = ?", (exam_id,))
        res = self.cursor.fetchone()
        return res[0] if res and res[0] is not None else 0

    def get_student_exam_stats(self, student_unique_id, class_name):
        # Get total exams for this class
        self.cursor.execute("SELECT COUNT(*) FROM Exams WHERE class_name = ?", (class_name,))
        total_exams = self.cursor.fetchone()[0]
        
        # Get exams attended by student in this class
        self.cursor.execute("""
            SELECT COUNT(*) FROM Marks m 
            JOIN Exams e ON m.exam_id = e.exam_id 
            WHERE m.student_unique_id = ? AND e.class_name = ?
        """, (student_unique_id, class_name))
        attended = self.cursor.fetchone()[0]
        missed = total_exams - attended
        return total_exams, attended, missed

    # --- Payment Operations ---
    def get_payments_for_student(self, student_unique_id):
        self.cursor.execute("SELECT * FROM Payments WHERE student_unique_id = ? ORDER BY year DESC, month DESC", (student_unique_id,))
        return self.cursor.fetchall()

    def add_payment(self, student_unique_id, class_name, month, year, amount, paid_status='paid'):
        self.cursor.execute("SELECT payment_id FROM Payments WHERE student_unique_id = ? AND month = ? AND year = ?", 
                            (student_unique_id, month, year))
        result = self.cursor.fetchone()
        if result:
            self.cursor.execute("UPDATE Payments SET paid_status = ?, amount = ? WHERE payment_id = ?", (paid_status, amount, result[0]))
        else:
            self.cursor.execute("""
                INSERT INTO Payments (student_unique_id, class_name, month, year, amount, paid_status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (student_unique_id, class_name, month, year, amount, paid_status))
        self.conn.commit()

    # --- Promotion Operations ---
    def promote_student(self, student_unique_id, new_class, overall_summary=""):
        self.cursor.execute("SELECT current_class FROM Students WHERE unique_student_id = ?", (student_unique_id,))
        res = self.cursor.fetchone()
        if not res: return
        old_class = res[0]
        current_year = str(datetime.datetime.now().year)
        
        # Insert into promotion history
        self.cursor.execute("""
            INSERT INTO PromotionHistory (student_unique_id, old_class, new_class, year, overall_result_summary)
            VALUES (?, ?, ?, ?, ?)
        """, (student_unique_id, old_class, new_class, current_year, overall_summary))
        
        # Update current class
        self.cursor.execute("UPDATE Students SET current_class = ? WHERE unique_student_id = ?", (new_class, student_unique_id))
        self.conn.commit()

    def get_promotion_history(self, student_unique_id):
        self.cursor.execute("SELECT * FROM PromotionHistory WHERE student_unique_id = ? ORDER BY year DESC", (student_unique_id,))
        return self.cursor.fetchall()

    # --- Reporting Operations ---
    def get_total_students(self):
        self.cursor.execute("SELECT COUNT(*) FROM Students WHERE status = 'active'")
        return self.cursor.fetchone()[0]

    def get_total_batches(self):
        self.cursor.execute("SELECT COUNT(*) FROM Classes")
        return self.cursor.fetchone()[0]

    def get_total_exams(self):
        self.cursor.execute("SELECT COUNT(*) FROM Exams")
        return self.cursor.fetchone()[0]

    def get_total_revenue(self):
        current_year = str(datetime.datetime.now().year)
        self.cursor.execute("SELECT SUM(amount) FROM Payments WHERE year = ? AND paid_status = 'paid'", (current_year,))
        res = self.cursor.fetchone()
        return res[0] if res and res[0] else 0.0

    def get_total_payments(self):
        current_year = str(datetime.datetime.now().year)
        self.cursor.execute("SELECT COUNT(*) FROM Payments WHERE year = ? AND paid_status = 'paid'", (current_year,))
        return self.cursor.fetchone()[0]

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    db = Database()
    print("Database initialized successfully.")
    db.close()
