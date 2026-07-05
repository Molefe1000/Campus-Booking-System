# Smart Campus resource, booking system
# This system will enable new users to create accounts and login
# This system will allow Campuses resources to be booked by users

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import hashlib


# Database Class
# if the database does not exist, it is created by the class
class Database:
    def __init__(self, db_name="campus_booking.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """In this STEP, We create all necessary tables needed on the database"""
        # Creation of Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                campus_id INTEGER,
                full_name TEXT
            )
        ''')

        # Creation of the Campuses table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS campuses (
                campus_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                location TEXT,
                max_booking_duration INTEGER DEFAULT 2,
                restricted_hours_start TEXT DEFAULT '08:00',
                restricted_hours_end TEXT DEFAULT '20:00',
                priority_access TEXT DEFAULT 'none'
            )
        ''')

        # Creation of the Resources table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS resources (
                resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                type TEXT,
                campus_id INTEGER,
                is_available INTEGER DEFAULT 1,
                FOREIGN KEY (campus_id) REFERENCES campuses(campus_id)
            )
        ''')

        # Creation of the bookings table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER,
                user_id INTEGER,
                booking_date TEXT,
                start_time TEXT,
                duration INTEGER,
                status TEXT DEFAULT 'active',
                created_at TEXT,
                FOREIGN KEY (resource_id) REFERENCES resources(resource_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        self.conn.commit()
        self.insert_default_data()

    def insert_default_data(self):
        """Push and Insert default campuses and admin users into the created database"""
        # Inserting default campuses into the created tables
        campuses = [
            ("Main Campus", "Downtown", 2, "08:00", "20:00", "none"),
            ("East Campus", "East Side", 3, "09:00", "22:00", "lecturer"),
            ("West Campus", "West Side", 4, "07:00", "18:00", "none")
        ]

        for campus in campuses:
            self.cursor.execute('''
                INSERT OR IGNORE INTO campuses 
                (name, location, max_booking_duration, restricted_hours_start, restricted_hours_end, priority_access)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', campus)

        # Creating and Inserting Default Users: (admins, campus admins and lecturers)
        users = [
            ("super_admin", hashlib.sha256("admin123".encode()).hexdigest(), "system_operator", None, "System Operator"),
            ("campus_admin1", hashlib.sha256("admin123".encode()).hexdigest(), "campus_admin", 1, "Main Campus Admin"),
            ("campus_admin2", hashlib.sha256("admin123".encode()).hexdigest(), "campus_admin", 2, "East Campus Admin"),
            ("campus_admin3", hashlib.sha256("admin123".encode()).hexdigest(), "campus_admin", 3, "West Campus Admin"),
            ("lecturer1", hashlib.sha256("lect123".encode()).hexdigest(), "lecturer", 1, "Dr. Magudumane"),
            ("lecturer1", hashlib.sha256("lect123".encode()).hexdigest(), "lecturer", 2, "Prof. Mokgethi"),
        ]

        for user in users:
            self.cursor.execute('''
                INSERT OR IGNORE INTO users (username, password, role, campus_id, full_name)
                VALUES (?, ?, ?, ?, ?)
            ''', user)

        # Inserting default campus resources into the database
        resources = [
            ("R001", "Lecture Hall A", "Auditorium", 1, 1),
            ("R002", "Computer Lab 1", "Lab", 1, 1),
            ("R003", "Meeting Room 1", "Conference", 1, 1),
            ("R004", "Lecture Hall B", "Auditorium", 2, 1),
            ("R005", "Science Lab", "Lab", 2, 1),
            ("R006", "Library Study Room", "Study", 3, 1),
            ("R007", "Seminar Room", "Conference", 3, 1),
        ]

        for resource in resources:
            self.cursor.execute('''
                INSERT OR IGNORE INTO resources (resource_code, name, type, campus_id, is_available)
                VALUES (?, ?, ?, ?, ?)
            ''', resource)

        self.conn.commit()

    def authenticate_user(self, username, password):
        """Function to Authenticate the users at login"""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute('''
            SELECT user_id, username, role, campus_id, full_name 
            FROM users 
            WHERE username = ? AND password = ?
        ''', (username, hashed_password))
        return self.cursor.fetchone()

    def register_user(self, username, password, full_name, role, campus_id=None):
        """Registration of a new user into the application"""
        # Check if username already exists
        self.cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        if self.cursor.fetchone():
            return False, "Username already exists. Please choose another."

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        try:
            self.cursor.execute('''
                INSERT INTO users (username, password, role, campus_id, full_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, hashed_password, role, campus_id, full_name))
            self.conn.commit()
            return True, "Registration successful! You can now login."
        except Exception as e:
            return False, f"Registration failed: {str(e)}"

    def get_campuses(self):
        """Function to Get all campuses"""
        self.cursor.execute("SELECT campus_id, name, location FROM campuses")
        return self.cursor.fetchall()

    def get_campus_by_id(self, campus_id):
        """Function to get campus details by ID"""
        self.cursor.execute("SELECT * FROM campuses WHERE campus_id = ?", (campus_id,))
        return self.cursor.fetchone()

    def get_resources_by_campus(self, campus_id):
        """Function to Get all resources for a specific campus"""
        self.cursor.execute('''
            SELECT resource_id, resource_code, name, type, is_available 
            FROM resources 
            WHERE campus_id = ?
            ORDER BY resource_code
        ''', (campus_id,))
        return self.cursor.fetchall()

    def add_resource(self, resource_code, name, resource_type, campus_id):
        """Adding a new resource"""
        try:
            self.cursor.execute('''
                INSERT INTO resources (resource_code, name, type, campus_id, is_available)
                VALUES (?, ?, ?, ?, 1)
            ''', (resource_code, name, resource_type, campus_id))
            self.conn.commit()
            return True, "Resource added successfully"
        except sqlite3.IntegrityError:
            return False, "Resource code already exists"

    def update_resource(self, resource_id, name, resource_type):
        """Updating resource information"""
        self.cursor.execute('''
            UPDATE resources 
            SET name = ?, type = ?
            WHERE resource_id = ?
        ''', (name, resource_type, resource_id))
        self.conn.commit()
        return True, "Resource updated successfully"

    def remove_resource(self, resource_id):
        """Remove a resource"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM bookings 
            WHERE resource_id = ? AND status = 'active'
        ''', (resource_id,))
        count = self.cursor.fetchone()[0]

        if count > 0:
            return False, "Cannot delete resource with active bookings"

        self.cursor.execute("DELETE FROM resources WHERE resource_id = ?", (resource_id,))
        self.conn.commit()
        return True, "Resource removed successfully"

    def check_availability(self, resource_id, booking_date, start_time, duration):
        """Check if a resource is available for booking"""
        start_hour = int(start_time.split(':')[0])
        start_min = int(start_time.split(':')[1])
        end_hour = start_hour + duration
        end_time = f"{end_hour:02d}:{start_min:02d}"

        self.cursor.execute('''
            SELECT COUNT(*) FROM bookings 
            WHERE resource_id = ? 
            AND booking_date = ? 
            AND status = 'active'
            AND start_time < ? AND ? > start_time
        ''', (resource_id, booking_date, end_time, start_time))

        count = self.cursor.fetchone()[0]
        return count == 0

    def create_booking(self, resource_id, user_id, booking_date, start_time, duration):
        """Create a new booking"""
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO bookings (resource_id, user_id, booking_date, start_time, duration, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?)
        ''', (resource_id, user_id, booking_date, start_time, duration, created_at))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_user_bookings(self, user_id):
        """Get all bookings for a user"""
        self.cursor.execute('''
            SELECT b.booking_id, b.booking_date, b.start_time, b.duration, b.status,
                   r.name, r.resource_code, c.name as campus_name
            FROM bookings b
            JOIN resources r ON b.resource_id = r.resource_id
            JOIN campuses c ON r.campus_id = c.campus_id
            WHERE b.user_id = ?
            ORDER BY b.booking_date DESC, b.start_time DESC
        ''', (user_id,))
        return self.cursor.fetchall()

    def get_campus_bookings(self, campus_id):
        """Get all bookings for a specific campus"""
        self.cursor.execute('''
            SELECT b.booking_id, b.booking_date, b.start_time, b.duration, b.status,
                   r.name, r.resource_code, u.full_name as user_name
            FROM bookings b
            JOIN resources r ON b.resource_id = r.resource_id
            JOIN users u ON b.user_id = u.user_id
            WHERE r.campus_id = ?
            ORDER BY b.booking_date DESC, b.start_time DESC
        ''', (campus_id,))
        return self.cursor.fetchall()

    def cancel_booking(self, booking_id):
        """Cancel a booking"""
        self.cursor.execute('''
            UPDATE bookings 
            SET status = 'cancelled' 
            WHERE booking_id = ?
        ''', (booking_id,))
        self.conn.commit()
        return True

    def get_campus_reports(self, campus_id):
        """Generate reports for a specific campus"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM bookings b
            JOIN resources r ON b.resource_id = r.resource_id
            WHERE r.campus_id = ? AND b.status = 'active'
        ''', (campus_id,))
        total_bookings = self.cursor.fetchone()[0]

        self.cursor.execute('''
            SELECT r.name, COUNT(*) as booking_count
            FROM bookings b
            JOIN resources r ON b.resource_id = r.resource_id
            WHERE r.campus_id = ? AND b.status = 'active'
            GROUP BY r.resource_id
            ORDER BY booking_count DESC
            LIMIT 5
        ''', (campus_id,))
        frequent_resources = self.cursor.fetchall()

        self.cursor.execute('''
            SELECT AVG(duration) FROM bookings b
            JOIN resources r ON b.resource_id = r.resource_id
            WHERE r.campus_id = ? AND b.status = 'active'
        ''', (campus_id,))
        avg_duration = self.cursor.fetchone()[0] or 0

        return {
            'total_bookings': total_bookings,
            'frequent_resources': frequent_resources,
            'avg_duration': round(avg_duration, 2)
        }

    def get_all_campuses_report(self):
        """Get report data for all campuses"""
        campuses = self.get_campuses()
        reports = []
        for campus in campuses:
            report = self.get_campus_reports(campus[0])
            reports.append({
                'campus_name': campus[1],
                **report
            })
        return reports

    def close(self):
        """Close database connection"""
        self.conn.close()


# ==================== BOOKING RULES CLASS ====================
class BookingRuleChecker:
    @staticmethod
    def validate_booking(campus_data, booking_date, start_time, duration):
        campus_id, name, location, max_duration, restrict_start, restrict_end, priority = campus_data

        if duration > max_duration:
            return False, f"Maximum booking duration for {name} is {max_duration} hours"

        booking_time = datetime.strptime(start_time, "%H:%M").time()
        start_time_obj = datetime.strptime(restrict_start, "%H:%M").time()
        end_time_obj = datetime.strptime(restrict_end, "%H:%M").time()

        if booking_time < start_time_obj or booking_time >= end_time_obj:
            return False, f"Bookings at {name} are only allowed between {restrict_start} and {restrict_end}"

        if priority == "lecturer":
            booking_datetime = datetime.strptime(booking_date, "%Y-%m-%d")
            if booking_datetime.weekday() >= 5:
                return True, "Weekend booking - lecturers have priority access"

        return True, "Booking rules satisfied"

    @staticmethod
    def get_rules_description(campus_name, campus_data):
        if not campus_data:
            return "No rules defined"

        max_duration = campus_data[3]
        restrict_start = campus_data[4]
        restrict_end = campus_data[5]
        priority = campus_data[6]

        rules = f"Rules for {campus_name}:\n"
        rules += f"• Maximum duration: {max_duration} hours\n"
        rules += f"• Booking hours: {restrict_start} - {restrict_end}\n"

        if priority == "lecturer":
            rules += "• Priority: Lecturers have weekend priority access\n"
        else:
            rules += "• Priority: Standard access for all users\n"

        return rules


# ==================== REGISTRATION WINDOW ====================
class RegistrationWindow:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
        self.window = tk.Toplevel(parent)
        self.window.title("Register New User")
        self.window.geometry("500x550")
        self.window.resizable(False, False)
        self.window.grab_set()  # Make it modal

        self.setup_ui()

    def setup_ui(self):
        # Title
        title_label = tk.Label(self.window, text="Create New Account",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=20)

        # Form Frame
        form_frame = tk.Frame(self.window)
        form_frame.pack(pady=10, padx=30, fill="both")

        # Full Name
        tk.Label(form_frame, text="Full Name:", font=("Arial", 11)).grid(row=0, column=0, pady=10, padx=10, sticky="w")
        self.full_name_entry = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.full_name_entry.grid(row=0, column=1, pady=10, padx=10)

        # Username
        tk.Label(form_frame, text="Username:", font=("Arial", 11)).grid(row=1, column=0, pady=10, padx=10, sticky="w")
        self.username_entry = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.username_entry.grid(row=1, column=1, pady=10, padx=10)

        # Password
        tk.Label(form_frame, text="Password:", font=("Arial", 11)).grid(row=2, column=0, pady=10, padx=10, sticky="w")
        self.password_entry = tk.Entry(form_frame, show="*", font=("Arial", 11), width=30)
        self.password_entry.grid(row=2, column=1, pady=10, padx=10)

        # Confirm Password
        tk.Label(form_frame, text="Confirm Password:", font=("Arial", 11)).grid(row=3, column=0, pady=10, padx=10,
                                                                                sticky="w")
        self.confirm_password_entry = tk.Entry(form_frame, show="*", font=("Arial", 11), width=30)
        self.confirm_password_entry.grid(row=3, column=1, pady=10, padx=10)

        # Role
        tk.Label(form_frame, text="Role:", font=("Arial", 11)).grid(row=4, column=0, pady=10, padx=10, sticky="w")
        self.role_var = tk.StringVar(value="lecturer")
        role_frame = tk.Frame(form_frame)
        role_frame.grid(row=4, column=1, pady=10, padx=10, sticky="w")

        tk.Radiobutton(role_frame, text="Lecturer", variable=self.role_var, value="lecturer",
                       font=("Arial", 10), command=self.toggle_campus_selection).pack(side="left", padx=5)
        tk.Radiobutton(role_frame, text="Campus Admin", variable=self.role_var, value="campus_admin",
                       font=("Arial", 10), command=self.toggle_campus_selection).pack(side="left", padx=5)

        # Campus Selection (only for campus_admin and lecturer)
        tk.Label(form_frame, text="Campus:", font=("Arial", 11)).grid(row=5, column=0, pady=10, padx=10, sticky="w")
        self.campus_combo = ttk.Combobox(form_frame, width=27, state="readonly")
        self.campus_combo.grid(row=5, column=1, pady=10, padx=10)

        # Load campuses into combobox
        campuses = self.db.get_campuses()
        self.campus_list = [(c[0], c[1]) for c in campuses]
        self.campus_combo['values'] = [c[1] for c in self.campus_list]
        if self.campus_list:
            self.campus_combo.current(0)

        # Note for users
        note_frame = tk.Frame(self.window, bg="#fff3cd", relief="solid", bd=1)
        note_frame.pack(fill="x", padx=30, pady=10)
        tk.Label(note_frame, text="Note: System Operator accounts can only be created by administrators.",
                 font=("Arial", 9), fg="#856404", bg="#fff3cd").pack(pady=5, padx=10)

        # Buttons Frame
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20)

        register_btn = tk.Button(button_frame, text="Register", command=self.register,
                                 bg="#4CAF50", fg="white", font=("Arial", 12), padx=30)
        register_btn.pack(side="left", padx=10)

        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.window.destroy,
                               bg="#f44336", fg="white", font=("Arial", 12), padx=30)
        cancel_btn.pack(side="left", padx=10)

    def toggle_campus_selection(self):
        """Enable/disable campus selection based on role"""
        if self.role_var.get() == "lecturer":
            self.campus_combo.config(state="readonly")
        else:
            self.campus_combo.config(state="readonly")

    def register(self):
        """Handle user registration"""
        full_name = self.full_name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        role = self.role_var.get()

        # Get selected campus ID
        selected_campus = self.campus_combo.get()
        campus_id = None
        for cid, name in self.campus_list:
            if name == selected_campus:
                campus_id = cid
                break

        # Validation
        if not full_name:
            messagebox.showerror("Error", "Please enter your full name")
            return

        if not username:
            messagebox.showerror("Error", "Please enter a username")
            return

        if len(username) < 3:
            messagebox.showerror("Error", "Username must be at least 3 characters long")
            return

        if not password:
            messagebox.showerror("Error", "Please enter a password")
            return

        if len(password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters long")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return

        if role in ["lecturer", "campus_admin"] and not campus_id:
            messagebox.showerror("Error", "Please select a campus")
            return

        # Register user
        success, message = self.db.register_user(username, password, full_name, role, campus_id)

        if success:
            messagebox.showinfo("Success", message)
            self.window.destroy()
        else:
            messagebox.showerror("Error", message)


# ==================== POP UP - TKINTER LOGIN WINDOW ====================
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Campus Resource Booking System - Login")
        self.root.geometry("450x450")
        self.root.resizable(False, False)

        self.db = Database()
        self.current_user = None

        self.setup_ui()

    def setup_ui(self):
        title_label = tk.Label(self.root, text="Smart Campus Resource Booking System",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=20)

        login_frame = tk.Frame(self.root)
        login_frame.pack(pady=30)

        tk.Label(login_frame, text="Username:", font=("Arial", 11)).grid(row=0, column=0, pady=10, padx=10)
        self.username_entry = tk.Entry(login_frame, font=("Arial", 11), width=20)
        self.username_entry.grid(row=0, column=1, pady=10)

        tk.Label(login_frame, text="Password:", font=("Arial", 11)).grid(row=1, column=0, pady=10, padx=10)
        self.password_entry = tk.Entry(login_frame, show="*", font=("Arial", 11), width=20)
        self.password_entry.grid(row=1, column=1, pady=10)

        # Buttons Frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)

        login_btn = tk.Button(button_frame, text="Login", command=self.login,
                              bg="#4CAF50", fg="white", font=("Arial", 12), padx=30)
        login_btn.pack(side="left", padx=10)

        # NEW: Register Button
        register_btn = tk.Button(button_frame, text="Register", command=self.open_registration,
                                 bg="#2196F3", fg="white", font=("Arial", 12), padx=30)
        register_btn.pack(side="left", padx=10)

        # Info Frame
        info_frame = tk.Frame(self.root, bg="#f0f0f0")
        info_frame.pack(pady=20, padx=20, fill="both")

        tk.Label(info_frame, text="\nLogin with your credentials OR Register a new account!",
                 font=("Arial", 9, "italic"), bg="#f0f0f0", fg="green").pack()

    def open_registration(self):
        """Open the registration window"""
        RegistrationWindow(self.root, self.db)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        user = self.db.authenticate_user(username, password)

        if user:
            self.current_user = {
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'campus_id': user[3],
                'full_name': user[4]
            }
            self.root.destroy()
            self.open_main_app()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def open_main_app(self):
        root = tk.Tk()
        app = MainApplication(root, self.db, self.current_user)
        root.mainloop()


# ==================== MAIN APPLICATION ====================
class MainApplication:
    def __init__(self, root, db, user):
        self.root = root
        self.db = db
        self.user = user
        self.current_campus = None

        self.root.title(f"Campus Resource Booking System - {user['full_name']}")
        self.root.geometry("1200x700")

        self.setup_menu()
        self.setup_main_frame()
        self.show_campus_selection()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Logout", command=self.logout)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.logout)

        if self.user['role'] == 'system_operator':
            reports_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Reports", menu=reports_menu)
            reports_menu.add_command(label="Cross-Campus Comparison", command=self.show_cross_campus_report)

    def setup_main_frame(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def show_campus_selection(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        if self.current_campus:
            campus_info = self.db.get_campus_by_id(self.current_campus)
            indicator_frame = tk.Frame(self.main_frame, bg="#4CAF50", height=40)
            indicator_frame.pack(fill="x", pady=(0, 10))
            tk.Label(indicator_frame, text=f"Current Campus: {campus_info[1]}",
                     font=("Arial", 12, "bold"), fg="white", bg="#4CAF50").pack(pady=5)

        select_frame = tk.LabelFrame(self.main_frame, text="Select Campus", font=("Arial", 12, "bold"))
        select_frame.pack(fill="both", expand=True, padx=20, pady=20)

        campuses = self.db.get_campuses()

        for campus in campuses:
            campus_frame = tk.Frame(select_frame, relief="ridge", bd=2, padx=10, pady=10)
            campus_frame.pack(fill="x", padx=10, pady=5)

            tk.Label(campus_frame, text=campus[1], font=("Arial", 14, "bold")).pack(anchor="w")
            tk.Label(campus_frame, text=f"Location: {campus[2]}", font=("Arial", 10)).pack(anchor="w")

            campus_data = self.db.get_campus_by_id(campus[0])
            rules_text = BookingRuleChecker.get_rules_description(campus[1], campus_data)
            tk.Label(campus_frame, text=rules_text, font=("Arial", 9), fg="gray", justify="left").pack(anchor="w")

            select_btn = tk.Button(campus_frame, text="Select Campus",
                                   command=lambda cid=campus[0]: self.select_campus(cid),
                                   bg="#2196F3", fg="white")
            select_btn.pack(pady=5)

    def select_campus(self, campus_id):
        self.current_campus = campus_id

        if self.user['role'] == 'lecturer':
            self.show_lecturer_dashboard()
        elif self.user['role'] == 'campus_admin':
            self.show_admin_dashboard()
        elif self.user['role'] == 'system_operator':
            self.show_operator_dashboard()

    def show_lecturer_dashboard(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        campus_data = self.db.get_campus_by_id(self.current_campus)

        indicator_frame = tk.Frame(self.main_frame, bg="#4CAF50", height=40)
        indicator_frame.pack(fill="x", pady=(0, 10))
        tk.Label(indicator_frame, text=f"Current Campus: {campus_data[1]} - Lecturer Dashboard",
                 font=("Arial", 12, "bold"), fg="white", bg="#4CAF50").pack(pady=5)

        rules_text = BookingRuleChecker.get_rules_description(campus_data[1], campus_data)
        rules_frame = tk.LabelFrame(self.main_frame, text="Campus Booking Rules", font=("Arial", 10, "bold"))
        rules_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(rules_frame, text=rules_text, font=("Arial", 9), justify="left").pack(pady=5, padx=10)

        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        book_frame = tk.Frame(notebook)
        notebook.add(book_frame, text="Book Resource")
        self.setup_book_resource_tab(book_frame, campus_data)

        bookings_frame = tk.Frame(notebook)
        notebook.add(bookings_frame, text="My Bookings")
        self.setup_my_bookings_tab(bookings_frame)

    def setup_book_resource_tab(self, parent, campus_data):
        tk.Label(parent, text="Select Resource:", font=("Arial", 11)).grid(row=0, column=0, pady=10, padx=10,
                                                                           sticky="w")

        self.resource_var = tk.StringVar()
        resources = self.db.get_resources_by_campus(self.current_campus)
        resource_list = [f"{r[1]} - {r[2]} ({r[3]})" for r in resources]
        self.resource_combo = ttk.Combobox(parent, textvariable=self.resource_var, values=resource_list, width=40)
        self.resource_combo.grid(row=0, column=1, pady=10, padx=10)

        tk.Label(parent, text="Booking Date (YYYY-MM-DD):", font=("Arial", 11)).grid(row=1, column=0, pady=10, padx=10,
                                                                                     sticky="w")
        self.date_var = tk.StringVar()
        self.date_entry = tk.Entry(parent, textvariable=self.date_var, width=25)
        self.date_entry.grid(row=1, column=1, pady=10, padx=10, sticky="w")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(parent, text="Start Time (HH:MM):", font=("Arial", 11)).grid(row=2, column=0, pady=10, padx=10,
                                                                              sticky="w")
        self.time_var = tk.StringVar()
        self.time_entry = tk.Entry(parent, textvariable=self.time_var, width=25)
        self.time_entry.grid(row=2, column=1, pady=10, padx=10, sticky="w")
        self.time_entry.insert(0, "09:00")

        tk.Label(parent, text="Duration (hours):", font=("Arial", 11)).grid(row=3, column=0, pady=10, padx=10,
                                                                            sticky="w")
        self.duration_var = tk.IntVar(value=1)
        self.duration_spin = tk.Spinbox(parent, from_=1, to=campus_data[3], textvariable=self.duration_var, width=10)
        self.duration_spin.grid(row=3, column=1, pady=10, padx=10, sticky="w")

        book_btn = tk.Button(parent, text="Book Resource", command=self.book_resource,
                             bg="#4CAF50", fg="white", font=("Arial", 12), padx=20)
        book_btn.grid(row=4, column=0, columnspan=2, pady=20)

    def book_resource(self):
        if not self.resource_var.get():
            messagebox.showwarning("Warning", "Please select a resource")
            return

        resource_text = self.resource_var.get()
        resource_code = resource_text.split(" - ")[0]
        resources = self.db.get_resources_by_campus(self.current_campus)
        resource_id = None
        for r in resources:
            if r[1] == resource_code:
                resource_id = r[0]
                break

        if not resource_id:
            messagebox.showerror("Error", "Resource not found")
            return

        booking_date = self.date_var.get()
        start_time = self.time_var.get()
        duration = self.duration_var.get()

        try:
            datetime.strptime(booking_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return

        try:
            datetime.strptime(start_time, "%H:%M")
        except ValueError:
            messagebox.showerror("Error", "Invalid time format. Use HH:MM")
            return

        campus_data = self.db.get_campus_by_id(self.current_campus)
        is_valid, message = BookingRuleChecker.validate_booking(campus_data, booking_date, start_time, duration)

        if not is_valid:
            messagebox.showerror("Booking Rules Violation", message)
            return

        if not self.db.check_availability(resource_id, booking_date, start_time, duration):
            messagebox.showerror("Error", "Resource is not available at the selected time")
            return

        booking_id = self.db.create_booking(resource_id, self.user['id'], booking_date, start_time, duration)

        if booking_id:
            messagebox.showinfo("Success", "Resource booked successfully!")
            self.show_lecturer_dashboard()
        else:
            messagebox.showerror("Error", "Failed to create booking")

    def setup_my_bookings_tab(self, parent):
        columns = ("ID", "Date", "Time", "Duration", "Resource", "Campus", "Status")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        bookings = self.db.get_user_bookings(self.user['id'])

        for booking in bookings:
            tree.insert("", "end", values=(
                booking[0], booking[1], booking[2], f"{booking[3]}h",
                booking[4], booking[5], booking[6]
            ))

        cancel_btn = tk.Button(parent, text="Cancel Selected Booking", command=lambda: self.cancel_booking(tree),
                               bg="#f44336", fg="white", font=("Arial", 11))
        cancel_btn.pack(pady=10)

    def cancel_booking(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a booking to cancel")
            return

        item = tree.item(selected[0])
        booking_id = item['values'][0]
        status = item['values'][6]

        if status != "active":
            messagebox.showwarning("Warning", "Only active bookings can be cancelled")
            return

        if messagebox.askyesno("Confirm", "Cancel this booking?"):
            self.db.cancel_booking(booking_id)
            messagebox.showinfo("Success", "Booking cancelled successfully")
            self.show_lecturer_dashboard()

    def show_admin_dashboard(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        campus_data = self.db.get_campus_by_id(self.current_campus)

        indicator_frame = tk.Frame(self.main_frame, bg="#4CAF50", height=40)
        indicator_frame.pack(fill="x", pady=(0, 10))
        tk.Label(indicator_frame, text=f"Current Campus: {campus_data[1]} - Campus Administrator Dashboard",
                 font=("Arial", 12, "bold"), fg="white", bg="#4CAF50").pack(pady=5)

        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        resources_frame = tk.Frame(notebook)
        notebook.add(resources_frame, text="Manage Resources")
        self.setup_manage_resources_tab(resources_frame)

        bookings_frame = tk.Frame(notebook)
        notebook.add(bookings_frame, text="Campus Bookings")
        self.setup_campus_bookings_tab(bookings_frame)

        reports_frame = tk.Frame(notebook)
        notebook.add(reports_frame, text="Campus Reports")
        self.setup_campus_reports_tab(reports_frame)

    def setup_manage_resources_tab(self, parent):
        columns = ("ID", "Code", "Name", "Type", "Status")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=10)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.refresh_resource_tree(tree)

        control_frame = tk.Frame(parent)
        control_frame.pack(fill="x", padx=10, pady=10)

        add_frame = tk.LabelFrame(control_frame, text="Add New Resource", font=("Arial", 10, "bold"))
        add_frame.pack(side="left", padx=5, fill="both", expand=True)

        tk.Label(add_frame, text="Code:").grid(row=0, column=0, padx=5, pady=5)
        self.code_entry = tk.Entry(add_frame, width=10)
        self.code_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(add_frame, text="Name:").grid(row=0, column=2, padx=5, pady=5)
        self.name_entry = tk.Entry(add_frame, width=20)
        self.name_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(add_frame, text="Type:").grid(row=0, column=4, padx=5, pady=5)
        self.type_combo = ttk.Combobox(add_frame, values=["Auditorium", "Lab", "Conference", "Study", "Classroom"],
                                       width=15)
        self.type_combo.grid(row=0, column=5, padx=5, pady=5)

        add_btn = tk.Button(add_frame, text="Add Resource",
                            command=lambda: self.add_resource(tree),
                            bg="#4CAF50", fg="white")
        add_btn.grid(row=0, column=6, padx=10, pady=5)

        update_frame = tk.LabelFrame(control_frame, text="Update/Delete Resource", font=("Arial", 10, "bold"))
        update_frame.pack(side="right", padx=5, fill="both", expand=True)

        tk.Label(update_frame, text="New Name:").pack(side="left", padx=5)
        self.update_name_entry = tk.Entry(update_frame, width=20)
        self.update_name_entry.pack(side="left", padx=5)

        tk.Label(update_frame, text="New Type:").pack(side="left", padx=5)
        self.update_type_combo = ttk.Combobox(update_frame,
                                              values=["Auditorium", "Lab", "Conference", "Study", "Classroom"],
                                              width=15)
        self.update_type_combo.pack(side="left", padx=5)

        update_btn = tk.Button(update_frame, text="Update",
                               command=lambda: self.update_resource(tree),
                               bg="#2196F3", fg="white")
        update_btn.pack(side="left", padx=5)

        delete_btn = tk.Button(update_frame, text="Delete",
                               command=lambda: self.delete_resource(tree),
                               bg="#f44336", fg="white")
        delete_btn.pack(side="left", padx=5)

    def refresh_resource_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

        resources = self.db.get_resources_by_campus(self.current_campus)
        for r in resources:
            status = "Available" if r[4] else "Unavailable"
            tree.insert("", "end", values=(r[0], r[1], r[2], r[3], status))

    def add_resource(self, tree):
        code = self.code_entry.get()
        name = self.name_entry.get()
        rtype = self.type_combo.get()

        if not code or not name or not rtype:
            messagebox.showwarning("Warning", "Please fill all fields")
            return

        success, message = self.db.add_resource(code, name, rtype, self.current_campus)
        if success:
            messagebox.showinfo("Success", message)
            self.refresh_resource_tree(tree)
            self.code_entry.delete(0, tk.END)
            self.name_entry.delete(0, tk.END)
            self.type_combo.set('')
        else:
            messagebox.showerror("Error", message)

    def update_resource(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a resource to update")
            return

        new_name = self.update_name_entry.get()
        new_type = self.update_type_combo.get()

        if not new_name or not new_type:
            messagebox.showwarning("Warning", "Please enter new name and type")
            return

        item = tree.item(selected[0])
        resource_id = item['values'][0]

        success, message = self.db.update_resource(resource_id, new_name, new_type)
        if success:
            messagebox.showinfo("Success", message)
            self.refresh_resource_tree(tree)
            self.update_name_entry.delete(0, tk.END)
            self.update_type_combo.set('')
        else:
            messagebox.showerror("Error", message)

    def delete_resource(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a resource to delete")
            return

        if messagebox.askyesno("Confirm", "Delete this resource? This action cannot be undone."):
            item = tree.item(selected[0])
            resource_id = item['values'][0]

            success, message = self.db.remove_resource(resource_id)
            if success:
                messagebox.showinfo("Success", message)
                self.refresh_resource_tree(tree)
            else:
                messagebox.showerror("Error", message)

    def setup_campus_bookings_tab(self, parent):
        columns = ("ID", "Date", "Time", "Duration", "Resource", "User", "Status")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        bookings = self.db.get_campus_bookings(self.current_campus)

        for booking in bookings:
            tree.insert("", "end", values=(
                booking[0], booking[1], booking[2], f"{booking[3]}h",
                booking[5], booking[6], booking[4]
            ))

    def setup_campus_reports_tab(self, parent):
        report_data = self.db.get_campus_reports(self.current_campus)
        campus_data = self.db.get_campus_by_id(self.current_campus)

        report_frame = tk.Frame(parent)
        report_frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(report_frame, text=f"Report for {campus_data[1]}",
                 font=("Arial", 16, "bold")).pack(pady=10)

        stats_frame = tk.Frame(report_frame, relief="ridge", bd=2)
        stats_frame.pack(fill="x", pady=10)

        tk.Label(stats_frame, text=f"Total Bookings: {report_data['total_bookings']}",
                 font=("Arial", 12)).pack(pady=5, padx=10, anchor="w")
        tk.Label(stats_frame, text=f"Average Booking Duration: {report_data['avg_duration']} hours",
                 font=("Arial", 12)).pack(pady=5, padx=10, anchor="w")

        resources_frame = tk.LabelFrame(report_frame, text="Most Frequently Used Resources", font=("Arial", 12, "bold"))
        resources_frame.pack(fill="both", expand=True, pady=10)

        if report_data['frequent_resources']:
            for resource in report_data['frequent_resources']:
                tk.Label(resources_frame, text=f"• {resource[0]}: {resource[1]} bookings",
                         font=("Arial", 11)).pack(pady=5, padx=10, anchor="w")
        else:
            tk.Label(resources_frame, text="No bookings found", font=("Arial", 11)).pack(pady=10)

    def show_operator_dashboard(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        campus_data = self.db.get_campus_by_id(self.current_campus)

        indicator_frame = tk.Frame(self.main_frame, bg="#4CAF50", height=40)
        indicator_frame.pack(fill="x", pady=(0, 10))
        tk.Label(indicator_frame, text=f"Current Campus: {campus_data[1]} - System Operator Dashboard",
                 font=("Arial", 12, "bold"), fg="white", bg="#4CAF50").pack(pady=5)

        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        bookings_frame = tk.Frame(notebook)
        notebook.add(bookings_frame, text="Campus Bookings")
        self.setup_campus_bookings_tab(bookings_frame)

        reports_frame = tk.Frame(notebook)
        notebook.add(reports_frame, text="Campus Reports")
        self.setup_campus_reports_tab(reports_frame)

    def show_cross_campus_report(self):
        report_window = tk.Toplevel(self.root)
        report_window.title("Cross-Campus Comparison Report")
        report_window.geometry("800x600")

        reports = self.db.get_all_campuses_report()

        notebook = ttk.Notebook(report_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        for report in reports:
            campus_frame = tk.Frame(notebook)
            notebook.add(campus_frame, text=report['campus_name'])

            tk.Label(campus_frame, text=f"Report for {report['campus_name']}",
                     font=("Arial", 14, "bold")).pack(pady=10)

            stats_frame = tk.Frame(campus_frame, relief="ridge", bd=2)
            stats_frame.pack(fill="x", pady=10, padx=20)

            tk.Label(stats_frame, text=f"Total Bookings: {report['total_bookings']}",
                     font=("Arial", 11)).pack(pady=5, padx=10, anchor="w")
            tk.Label(stats_frame, text=f"Average Duration: {report['avg_duration']} hours",
                     font=("Arial", 11)).pack(pady=5, padx=10, anchor="w")

            resources_frame = tk.LabelFrame(campus_frame, text="Most Used Resources", font=("Arial", 11, "bold"))
            resources_frame.pack(fill="both", expand=True, pady=10, padx=20)

            for resource in report['frequent_resources']:
                tk.Label(resources_frame, text=f"• {resource[0]}: {resource[1]} bookings",
                         font=("Arial", 10)).pack(pady=3, padx=10, anchor="w")

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.root.destroy()
            root = tk.Tk()
            LoginWindow(root)
            root.mainloop()


# ==================== MAIN ENTRY POINT ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()