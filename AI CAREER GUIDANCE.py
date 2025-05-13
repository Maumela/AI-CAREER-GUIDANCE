import sys
import serial.tools.list_ports
import psycopg2
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QFrame, QFormLayout, QMessageBox, QTextEdit,
                             QTableWidget, QTableWidgetItem, QComboBox, QRadioButton,
                             QHBoxLayout, QButtonGroup, QHeaderView, QDialog, QDialogButtonBox,
                             QStackedWidget, QScrollArea, QTabWidget, QSplitter)
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import (QPixmap, QFont, QColor, QIntValidator, QRegularExpressionValidator,
                         QPalette, QFontDatabase, QIcon)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRegularExpression, QUrl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import serial
import time
from twilio.rest import Client

# Database connection constants
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "career123"
DB_USER = "postgres"
DB_PASSWORD = "Maumela@20"

# Twilio credentials
TWILIO_ACCOUNT_SID = "ACcb171ed99aa0ba42e751102817f6ea7b"
TWILIO_AUTH_TOKEN = "a6803bb4021d9c5f4e09e43f215105f9"
TWILIO_PHONE_NUMBER = "+17542033966"

# Color scheme - Professional with cute accents
PRIMARY_COLOR = "#2c3e50"     # Dark blue-gray
SECONDARY_COLOR = "#34495e"   # Slightly lighter blue-gray
BACKGROUND_COLOR = "#f5f7fa"  # Very light gray
ACCENT_COLOR = "#3498db"      # Bright blue
LIGHT_ACCENT = "#5dade2"      # Lighter blue
SUCCESS_COLOR = "#27ae60"     # Green
WARNING_COLOR = "#f39c12"     # Orange
ERROR_COLOR = "#e74c3c"       # Red
HIGHLIGHT_COLOR = "#f1c40f"   # Yellow

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

def initialize_database():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'students'
                    );
                """)
                table_exists = cursor.fetchone()[0]

                if not table_exists:
                    cursor.execute("""
                        CREATE TABLE students (
                            student_id SERIAL PRIMARY KEY,
                            surname VARCHAR(100) NOT NULL,
                            name VARCHAR(100) NOT NULL,
                            age INTEGER CHECK (age > 0),
                            grade VARCHAR(20) NOT NULL,
                            school VARCHAR(200) NOT NULL,
                            phone VARCHAR(20) CHECK (LENGTH(phone) = 10),
                            career TEXT,
                            gender VARCHAR(10),
                            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                else:
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='students' AND column_name='registration_date'
                    """)
                    if not cursor.fetchone():
                        cursor.execute("""
                            ALTER TABLE students 
                            ADD COLUMN registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        """)
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error initializing database: {e}")
        finally:
            conn.close()

initialize_database()

class QuizThread(QThread):
    answer_signal = pyqtSignal(str)
    prediction_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def run(self):
        try:
            arduino = serial.Serial('COM6', 9600, timeout=10)
            time.sleep(2)
            arduino.write(b'START\n')

            while True:
                line = arduino.readline().decode().strip()
                if line.startswith("Answer:"):
                    self.answer_signal.emit(line)
                elif line.startswith("PREDICTION:"):
                    self.prediction_signal.emit(line.split("PREDICTION:")[1].strip())
                    break
            arduino.close()
        except Exception as e:
            self.error_signal.emit(str(e))

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("University of Limpopo - Career Guidance System")
        self.showFullScreen()
        self.init_ui()

    def init_ui(self):
        # Create main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left side - Decorative image/illustration
        left_widget = QWidget()
        left_widget.setStyleSheet(f"background-color: {ACCENT_COLOR};")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Decorative illustration placeholder (could be replaced with actual image)
        illustration = QLabel()
        illustration.setAlignment(Qt.AlignmentFlag.AlignCenter)
        illustration.setPixmap(QPixmap("career_illustration.png").scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio))
        illustration.setStyleSheet("background-color: transparent;")
        
        # Add some decorative elements
        title_left = QLabel("Discover Your Future")
        title_left.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_left.setStyleSheet(f"color: white;")
        title_left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_left = QLabel("Find your perfect career path with our guidance system")
        subtitle_left.setFont(QFont("Arial", 14))
        subtitle_left.setStyleSheet(f"color: white;")
        subtitle_left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        left_layout.addStretch()
        left_layout.addWidget(title_left)
        left_layout.addWidget(subtitle_left)
        left_layout.addWidget(illustration)
        left_layout.addStretch()
        
        # Right side - Login form
        right_widget = QWidget()
        right_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {BACKGROUND_COLOR};
            }}
            QLabel {{
                color: {PRIMARY_COLOR};
                font-size: 16px;
            }}
            QLineEdit {{
                padding: 12px;
                border: 2px solid {SECONDARY_COLOR};
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                color: {PRIMARY_COLOR};
            }}
            QPushButton {{
                padding: 12px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                background-color: {ACCENT_COLOR};
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_ACCENT};
            }}
            QRadioButton {{
                font-size: 14px;
                color: {PRIMARY_COLOR};
            }}
            QFrame {{
                background-color: white;
                border-radius: 12px;
                padding: 30px;
                border: 1px solid #e0e0e0;
            }}
        """)
        
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(40, 40, 40, 40)
        right_layout.setSpacing(20)
        
        # University logo
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setPixmap(QPixmap("ul_logo.png").scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
        
        # Title
        title = QLabel("Career Guidance System")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {PRIMARY_COLOR};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Welcome message
        welcome = QLabel("Welcome to the University of Limpopo Career Guidance System")
        welcome.setFont(QFont("Arial", 14))
        welcome.setStyleSheet(f"color: {SECONDARY_COLOR};")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Form frame
        form_frame = QFrame()
        frame_layout = QVBoxLayout(form_frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(20)
        
        # Form
        form = QFormLayout()
        form.setVerticalSpacing(15)
        
        # Input validation for username and password
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        form.addRow("Username:", self.username_input)
        form.addRow("Password:", self.password_input)
        
        # Login type
        self.login_type = QButtonGroup(self)
        self.user_login_radio = QRadioButton("Student Login")
        self.admin_login_radio = QRadioButton("Admin Login")
        self.user_login_radio.setChecked(True)
        self.login_type.addButton(self.user_login_radio)
        self.login_type.addButton(self.admin_login_radio)
        
        type_layout = QHBoxLayout()
        type_layout.addWidget(self.user_login_radio)
        type_layout.addWidget(self.admin_login_radio)
        
        # Buttons
        self.login_button = QPushButton("Login")
        self.login_button.setIcon(QIcon("login_icon.png"))  # Add an icon if available
        self.login_button.clicked.connect(self.check_login)
        
        self.view_chart_button = QPushButton("View Career Statistics")
        self.view_chart_button.setStyleSheet(f"background-color: {SECONDARY_COLOR}; color: white;")
        self.view_chart_button.clicked.connect(self.view_chart)
        
        # Add to frame layout
        frame_layout.addLayout(form)
        frame_layout.addWidget(QLabel("Login Type:"))
        frame_layout.addLayout(type_layout)
        frame_layout.addWidget(self.login_button)
        frame_layout.addWidget(self.view_chart_button)
        
        # Add to right layout
        right_layout.addWidget(logo)
        right_layout.addWidget(title)
        right_layout.addWidget(welcome)
        right_layout.addWidget(form_frame)
        right_layout.addStretch()
        
        # Add left and right widgets to main layout
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 1)
        
        self.setLayout(main_layout)

    def check_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if self.user_login_radio.isChecked():
            if username == "user" and password == "user":
                self.student_register_window = StudentRegisterWindow()
                self.student_register_window.show()
                self.close()
            else:
                QMessageBox.critical(self, "Login Error", "Incorrect credentials for student login.")
        
        elif self.admin_login_radio.isChecked():
            if username == "admin" and password == "admin":
                self.admin_window = AdminWindow()
                self.admin_window.show()
                self.close()
            else:
                QMessageBox.critical(self, "Login Error", "Incorrect credentials for admin login.")

    def view_chart(self):
        self.chart_window = CareerChart()
        self.chart_window.show()

# [Rest of your classes (AdminWindow, StudentRegisterWindow, CareerChart) remain the same]
# Only the styling needs to be updated to match the new color scheme

class AdminWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin - Student Database")
        self.setGeometry(100, 100, 1200, 700)
        self.selected_student_id = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BACKGROUND_COLOR};
                font-family: Arial;
            }}
            QLabel {{
                color: {PRIMARY_COLOR};
                font-size: 16px;
            }}
            QPushButton {{
                padding: 8px 12px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                background-color: {ACCENT_COLOR};
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_ACCENT};
            }}
            QTableWidget {{
                background-color: white;
                border: 1px solid #e0e0e0;
                font-size: 14px;
                color: {PRIMARY_COLOR};
                gridline-color: #e0e0e0;
            }}
            QLineEdit, QComboBox {{
                padding: 8px;
                border: 2px solid {SECONDARY_COLOR};
                border-radius: 5px;
                font-size: 14px;
                background-color: white;
                color: {PRIMARY_COLOR};
            }}
            QHeaderView::section {{
                background-color: {SECONDARY_COLOR};
                color: white;
                padding: 5px;
                border: none;
                font-weight: bold;
            }}
            QRadioButton {{
                font-size: 14px;
                color: {PRIMARY_COLOR};
            }}
            QDialog {{
                background-color: {BACKGROUND_COLOR};
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Student Database Management")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {PRIMARY_COLOR};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search students...")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.load_student_data)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.back_button = QPushButton("Back to Login")
        self.back_button.setStyleSheet(f"background-color: {SECONDARY_COLOR}; color: white;")
        self.back_button.clicked.connect(self.go_back)
        
        self.edit_button = QPushButton("Edit Student")
        self.edit_button.clicked.connect(self.edit_student)
        
        self.delete_button = QPushButton("Delete Student")
        self.delete_button.setStyleSheet(f"background-color: {ERROR_COLOR}; color: white;")
        self.delete_button.clicked.connect(self.delete_student)
        
        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Surname", "Name", "Age", "Grade", "School", 
            "Phone", "Career", "Gender"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        self.table.setColumnHidden(0, True)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.load_student_data()

    def on_row_selected(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            id_item = self.table.item(selected_row, 0)
            if id_item and id_item.text().isdigit():
                self.selected_student_id = int(id_item.text())
            else:
                self.selected_student_id = None

    def load_student_data(self):
        search_term = self.search_input.text().strip()
        conn = get_db_connection()
        if not conn:
            QMessageBox.critical(self, "Error", "Database connection failed")
            return

        try:
            with conn.cursor() as cursor:
                if search_term:
                    cursor.execute("""
                        SELECT student_id, surname, name, age, grade, school, phone, career, gender 
                        FROM students 
                        WHERE surname ILIKE %s OR name ILIKE %s OR school ILIKE %s OR career ILIKE %s
                        ORDER BY student_id DESC
                    """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
                else:
                    cursor.execute("""
                        SELECT student_id, surname, name, age, grade, school, phone, career, gender 
                        FROM students 
                        ORDER BY student_id DESC
                    """)
                students = cursor.fetchall()

                self.table.setRowCount(len(students))
                for row_idx, student in enumerate(students):
                    for col_idx, value in enumerate(student):
                        item = QTableWidgetItem(str(value))
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        self.table.setItem(row_idx, col_idx, item)

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Error", f"Database error: {e}")
        finally:
            conn.close()

    def edit_student(self):
        if not self.selected_student_id:
            QMessageBox.warning(self, "Error", "Please select a student first")
            return

        conn = get_db_connection()
        if not conn:
            QMessageBox.critical(self, "Error", "Database connection failed")
            return

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT surname, name, age, grade, school, phone, career, gender 
                    FROM students 
                    WHERE student_id = %s
                """, (self.selected_student_id,))
                student = cursor.fetchone()

                if not student:
                    QMessageBox.warning(self, "Error", "Student not found")
                    return

                dialog = QDialog(self)
                dialog.setWindowTitle("Edit Student")
                dialog.setFixedSize(500, 500)
                
                layout = QVBoxLayout()
                form = QFormLayout()
                
                # Form fields with validation
                self.surname_edit = QLineEdit(student[0])
                self.surname_edit.setValidator(QRegularExpressionValidator(QRegularExpression("^[A-Za-z ]+$")))
                
                self.name_edit = QLineEdit(student[1])
                self.name_edit.setValidator(QRegularExpressionValidator(QRegularExpression("^[A-Za-z ]+$")))
                
                self.age_edit = QLineEdit(str(student[2]))
                self.age_edit.setValidator(QIntValidator(10, 25))
                
                self.grade_edit = QComboBox()
                self.grade_edit.addItems(["Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"])
                self.grade_edit.setCurrentText(student[3])
                
                self.school_edit = QLineEdit(student[4])
                self.school_edit.setValidator(QRegularExpressionValidator(QRegularExpression("^[A-Za-z0-9 ]+$")))
                
                self.phone_edit = QLineEdit(student[5] if student[5] else "")
                self.phone_edit.setValidator(QRegularExpressionValidator(QRegularExpression("^[0-9]{10}$")))
                self.career_edit = QLineEdit(student[6] if student[6] else "")
                
                self.gender_group = QButtonGroup()
                male = QRadioButton("Male")
                female = QRadioButton("Female")
                other = QRadioButton("Other")
                self.gender_group.addButton(male)
                self.gender_group.addButton(female)
                self.gender_group.addButton(other)
                
                if student[7] == "Male":
                    male.setChecked(True)
                elif student[7] == "Female":
                    female.setChecked(True)
                else:
                    other.setChecked(True)
                
                gender_layout = QHBoxLayout()
                gender_layout.addWidget(male)
                gender_layout.addWidget(female)
                gender_layout.addWidget(other)
                
                # Add to form
                form.addRow("Surname:", self.surname_edit)
                form.addRow("Name:", self.name_edit)
                form.addRow("Age:", self.age_edit)
                form.addRow("Grade:", self.grade_edit)
                form.addRow("School:", self.school_edit)
                form.addRow("Phone:", self.phone_edit)
                form.addRow("Career:", self.career_edit)
                form.addRow("Gender:", gender_layout)
                
                # Buttons
                buttons = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
                )
                buttons.accepted.connect(lambda: self.update_student(dialog))
                buttons.rejected.connect(dialog.reject)
                
                layout.addLayout(form)
                layout.addWidget(buttons)
                dialog.setLayout(layout)
                dialog.exec()
                
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Error", f"Database error: {e}")
        finally:
            conn.close()

    def update_student(self, dialog):
        # Validate inputs
        if not all([self.surname_edit.text(), self.name_edit.text(), self.age_edit.text(), self.school_edit.text()]):
            QMessageBox.warning(self, "Error", "Please fill all required fields")
            return

        try:
            age = int(self.age_edit.text())
            if age < 10 or age > 25:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Age must be between 10-25")
            return

        if self.phone_edit.text() and len(self.phone_edit.text()) != 10:
            QMessageBox.warning(self, "Error", "Phone must be 10 digits")
            return

        conn = get_db_connection()
        if not conn:
            QMessageBox.critical(self, "Error", "Database connection failed")
            return

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE students 
                    SET surname = %s, name = %s, age = %s, grade = %s, 
                        school = %s, phone = %s, career = %s, gender = %s
                    WHERE student_id = %s
                """, (
                    self.surname_edit.text(),
                    self.name_edit.text(),
                    int(self.age_edit.text()),
                    self.grade_edit.currentText(),
                    self.school_edit.text(),
                    self.phone_edit.text() or None,
                    self.career_edit.text() or None,
                    self.gender_group.checkedButton().text(),
                    self.selected_student_id
                ))
                conn.commit()
                QMessageBox.information(self, "Success", "Student updated")
                self.load_student_data()
                dialog.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Error", f"Database error: {e}")
        finally:
            conn.close()

    def delete_student(self):
        if not self.selected_student_id:
            QMessageBox.warning(self, "Error", "Please select a student first")
            return

        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            "Are you sure you want to delete this student?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            conn = get_db_connection()
            if not conn:
                QMessageBox.critical(self, "Error", "Database connection failed")
                return

            try:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM students WHERE student_id = %s", (self.selected_student_id,))
                    conn.commit()
                    QMessageBox.information(self, "Success", "Student deleted")
                    self.load_student_data()
            except psycopg2.Error as e:
                QMessageBox.critical(self, "Error", f"Database error: {e}")
            finally:
                conn.close()

    def go_back(self):
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

class StudentRegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Registration")
        self.setGeometry(100, 100, 900, 700)
        self.prediction = None
        self.twilio_client = None

        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            try:
                self.twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            except Exception as e:
                print(f"Twilio error: {e}")

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BACKGROUND_COLOR};
                font-family: Arial;
            }}
            QLabel {{
                color: {PRIMARY_COLOR};
                font-size: 16px;
            }}
            QLineEdit, QComboBox {{
                padding: 8px;
                border: 2px solid {SECONDARY_COLOR};
                border-radius: 5px;
                font-size: 14px;
                background-color: white;
                color: {PRIMARY_COLOR};
            }}
            QPushButton {{
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                background-color: {ACCENT_COLOR};
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_ACCENT};
            }}
            QTextEdit {{
                background-color: white;
                border: 2px solid {SECONDARY_COLOR};
                font-size: 14px;
                color: {PRIMARY_COLOR};
            }}
            QRadioButton {{
                font-size: 14px;
                color: {PRIMARY_COLOR};
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Student Registration")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {PRIMARY_COLOR};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Form
        form = QFormLayout()
        form.setVerticalSpacing(15)
        
        # Personal Info with validation
        self.surname_input = QLineEdit()
        self.surname_input.setValidator(QRegularExpressionValidator(QRegularExpression("^[A-Za-z ]+$")))
        
        self.name_input = QLineEdit()
        self.name_input.setValidator(QRegularExpressionValidator(QRegularExpression("^[A-Za-z ]+$")))
        
        self.age_input = QLineEdit()
        self.age_input.setValidator(QIntValidator(10, 25))
        self.age_input.setPlaceholderText("10-25")
        
        # School Info
        self.grade_input = QComboBox()
        self.grade_input.addItems(["Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"])
        self.school_input = QLineEdit()
        self.school_input.setValidator(QRegularExpressionValidator(QRegularExpression("^[A-Za-z ]+$")))
        
        # Contact Info
        self.phone_input = QLineEdit()
        self.phone_input.setValidator(QRegularExpressionValidator(QRegularExpression("^[0-9]{10}$")))
        self.phone_input.setPlaceholderText("10 digits")
        
        # Gender
        self.gender_group = QButtonGroup(self)
        male = QRadioButton("Male")
        female = QRadioButton("Female")
        other = QRadioButton("Other")
        self.gender_group.addButton(male)
        self.gender_group.addButton(female)
        self.gender_group.addButton(other)
        male.setChecked(True)
        
        gender_layout = QHBoxLayout()
        gender_layout.addWidget(male)
        gender_layout.addWidget(female)
        gender_layout.addWidget(other)
        
        # Add to form
        form.addRow("Surname*:", self.surname_input)
        form.addRow("Name*:", self.name_input)
        form.addRow("Age* (10-25):", self.age_input)
        form.addRow("Grade*:", self.grade_input)
        form.addRow("School*:", self.school_input)
        form.addRow("Phone:", self.phone_input)
        form.addRow("Gender*:", gender_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.register_button = QPushButton("Register & Start Quiz")
        self.register_button.clicked.connect(self.validate_and_start_quiz)
        
        self.back_button = QPushButton("Back")
        self.back_button.setStyleSheet(f"background-color: {SECONDARY_COLOR}; color: white;")
        self.back_button.clicked.connect(self.go_back)
        
        button_layout.addWidget(self.register_button)
        button_layout.addWidget(self.back_button)
        
        # Quiz Output
        self.answer_display = QTextEdit()
        self.answer_display.setReadOnly(True)
        self.answer_display.setPlaceholderText("Quiz answers will appear here...")
        
        self.prediction_display = QLabel("Career prediction will appear here...")
        self.prediction_display.setStyleSheet(f"""
            QLabel {{
                background-color: white;
                border: 2px solid {SECONDARY_COLOR};
                border-radius: 5px;
                padding: 15px;
                font-weight: bold;
                color: {PRIMARY_COLOR};
                font-size: 16px;
            }}
        """)
        self.prediction_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.view_chart_button = QPushButton("View Career Statistics")
        self.view_chart_button.setStyleSheet(f"background-color: {SECONDARY_COLOR}; color: white;")
        self.view_chart_button.clicked.connect(self.view_chart)
        
        # Add to main layout
        layout.addLayout(form)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("Quiz Answers:"))
        layout.addWidget(self.answer_display)
        layout.addWidget(QLabel("Career Prediction:"))
        layout.addWidget(self.prediction_display)
        layout.addWidget(self.view_chart_button)
        
        self.setLayout(layout)

    def validate_and_start_quiz(self):
        # Validate required fields
        if not all([
            self.surname_input.text(),
            self.name_input.text(),
            self.age_input.text(),
            self.school_input.text(),
            self.gender_group.checkedButton()
        ]):
            QMessageBox.warning(self, "Error", "Please fill all required fields (*)")
            return

        try:
            age = int(self.age_input.text())
            if age < 10 or age > 25:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Age must be between 10-25")
            return

        if self.phone_input.text() and len(self.phone_input.text()) != 10:
            QMessageBox.warning(self, "Error", "Phone must be 10 digits if provided")
            return

        # Start quiz
        self.answer_display.clear()
        self.prediction_display.setText("Waiting for prediction...")
        self.quiz_thread = QuizThread()
        self.quiz_thread.answer_signal.connect(self.answer_display.append)
        self.quiz_thread.prediction_signal.connect(self.handle_prediction)
        self.quiz_thread.error_signal.connect(lambda err: QMessageBox.critical(self, "Error", err))
        self.quiz_thread.start()

    def handle_prediction(self, prediction):
        self.prediction = prediction.strip()
        self.prediction_display.setText(f"Predicted Career: {self.prediction}")
        self.save_student()
        
        if self.phone_input.text():
            self.send_result_sms()

    def send_result_sms(self):
        if not self.twilio_client:
            QMessageBox.warning(self, "Error", "SMS service not available")
            return
            
        if not self.prediction:
            QMessageBox.warning(self, "Error", "No prediction to send")
            return
            
        reply = QMessageBox.question(
            self, 
            "Send SMS", 
            "Send career prediction via SMS?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                phone = f"+27{self.phone_input.text()[1:]}"  # SA format
                message = self.twilio_client.messages.create(
                    body=f"Hello {self.name_input.text()},\nYour career prediction: {self.prediction}",
                    from_=TWILIO_PHONE_NUMBER,
                    to=phone
                )
                QMessageBox.information(self, "Success", "SMS sent successfully")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to send SMS: {e}")

    def save_student(self):
        if not self.prediction:
            QMessageBox.warning(self, "Error", "No prediction to save")
            return

        conn = get_db_connection()
        if not conn:
            QMessageBox.critical(self, "Error", "Database connection failed")
            return

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO students 
                    (surname, name, age, grade, school, phone, career, gender) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    self.surname_input.text(),
                    self.name_input.text(),
                    int(self.age_input.text()),
                    self.grade_input.currentText(),
                    self.school_input.text(),
                    self.phone_input.text() or None,
                    self.prediction,
                    self.gender_group.checkedButton().text()
                ))
                conn.commit()
                QMessageBox.information(self, "Success", "Student registered successfully")
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Error", f"Database error: {e}")
        finally:
            conn.close()

    def view_chart(self):
        self.chart_window = CareerChart()
        self.chart_window.show()

    def go_back(self):
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

class CareerChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Career Predictions Chart")
        self.setGeometry(300, 200, 800, 600)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BACKGROUND_COLOR};
            }}
        """)
        self.plot_chart()

    def plot_chart(self):
        conn = get_db_connection()
        if not conn:
            QMessageBox.critical(self, "Error", "Database connection failed")
            return

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT career, COUNT(*) FROM students WHERE career IS NOT NULL GROUP BY career")
                data = cursor.fetchall()
                
                if not data:
                    QMessageBox.information(self, "Info", "No career data available")
                    return

                careers = [row[0] for row in data]
                counts = [row[1] for row in data]

                fig, ax = plt.subplots()
                colors = [ACCENT_COLOR, PRIMARY_COLOR, HIGHLIGHT_COLOR, SUCCESS_COLOR, WARNING_COLOR]
                ax.barh(careers, counts, color=colors)
                ax.set_xlabel("Number of Students", color=PRIMARY_COLOR)
                ax.set_ylabel("Careers", color=PRIMARY_COLOR)
                ax.set_title("Career Prediction Distribution", color=PRIMARY_COLOR)
                ax.tick_params(colors=PRIMARY_COLOR)
                fig.patch.set_facecolor(BACKGROUND_COLOR)
                ax.set_facecolor(BACKGROUND_COLOR)

                for spine in ax.spines.values():
                    spine.set_edgecolor(PRIMARY_COLOR)

                canvas = FigureCanvas(fig)
                layout = QVBoxLayout()
                layout.addWidget(canvas)
                self.setLayout(layout)

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Error", f"Database error: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())