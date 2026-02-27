import os
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp

from kivy.core.window import Window

from database import Database
from pdf_generator import generate_exam_result_pdf

# Set light background
Window.clearcolor = (0.95, 0.95, 0.95, 1)

# Apply global light theme rules
Builder.load_string('''
<Label>:
    color: 0.1, 0.1, 0.1, 1
<TextInput>:
    background_color: 1, 1, 1, 1
    foreground_color: 0.1, 0.1, 0.1, 1
<Button>:
    background_normal: ''
    background_color: 0.2, 0.5, 0.8, 1
    color: 1, 1, 1, 1
<Spinner>:
    background_normal: ''
    background_color: 0.2, 0.5, 0.8, 1
    color: 1, 1, 1, 1
''')

# Initialize Database global instance
db = Database()

def show_popup(title, message):
    layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
    layout.add_widget(Label(text=message))
    btn = Button(text="Close", size_hint_y=None, height=dp(40))
    layout.add_widget(btn)
    popup = Popup(title=title, content=layout, size_hint=(0.8, 0.4))
    btn.bind(on_release=popup.dismiss)
    popup.open()

# --- Screens ---
class LoginScreen(Screen):
    def do_login(self, username, password):
        if username == 'admin' and db.verify_admin(password):
            self.manager.current = 'dashboard'
            self.ids.error_msg.text = ''
            self.ids.username.text = ''
            self.ids.password.text = ''
        else:
            self.ids.error_msg.text = 'Invalid Credentials!'

class DashboardScreen(Screen):
    def logout(self):
        self.manager.current = 'login'

    def show_reports(self):
        self.manager.current = 'reports'

class BatchListScreen(Screen):
    def on_enter(self):
        self.ids.batch_grid.clear_widgets()
        classes = db.get_classes()
        for c in classes:
            btn = Button(text=c[1], size_hint_y=None, height=dp(60))
            btn.bind(on_release=lambda instance, class_name=c[1]: self.go_to_class(class_name))
            self.ids.batch_grid.add_widget(btn)

    def go_to_class(self, class_name):
        app = App.get_running_app()
        app.selected_class = class_name
        self.manager.current = 'class_management'


class ClassManagementScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        self.ids.title_label.text = f'Management - {app.selected_class}'
        self.load_students()

    def load_students(self):
        self.ids.students_list.clear_widgets()
        app = App.get_running_app()
        students = db.get_students_by_class(app.selected_class)
        for s in students:
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=5)
            row.add_widget(Label(text=s[1], size_hint_x=0.2)) # ID
            row.add_widget(Label(text=s[2], size_hint_x=0.5)) # Name
            row.add_widget(Label(text=s[8] if s[8] else "N/A", size_hint_x=0.15)) # Section
            
            btn = Button(text='View', size_hint_x=0.15, background_color=(0.2, 0.6, 0.8, 1))
            btn.bind(on_release=lambda instance, std_id=s[1]: self.view_student(std_id))
            row.add_widget(btn)

            self.ids.students_list.add_widget(row)

    def go_to_add_student(self):
        self.manager.current = 'add_student'

    def go_to_exams(self):
        # We will show a popup with exam options
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        btn_add = Button(text="Add New Exam")
        btn_view = Button(text="View Existing Exams / Enter Marks")
        
        layout.add_widget(btn_add)
        layout.add_widget(btn_view)
        
        popup = Popup(title="Exam Management", content=layout, size_hint=(0.8, 0.5))
        
        btn_add.bind(on_release=lambda x: self.open_add_exam(popup))
        btn_view.bind(on_release=lambda x: self.open_view_exams(popup))
        
        popup.open()
        
    def open_add_exam(self, popup):
        popup.dismiss()
        self.manager.current = 'add_exam'
        
    def open_view_exams(self, popup):
        popup.dismiss()
        app = App.get_running_app()
        exams = db.get_exams_by_class(app.selected_class)
        if not exams:
            show_popup("Exams", "No exams found for this class.")
            return
            
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        
        for e in exams:
            btn = Button(text=f"{e[2]} - {e[4]}", size_hint_y=None, height=dp(40))
            btn.bind(on_release=lambda instance, exam_id=e[0]: self.open_marks_entry(exam_id, popup2))
            grid.add_widget(btn)
            
        popup2 = Popup(title="Select Exam", content=grid, size_hint=(0.8, 0.8))
        popup2.open()
        
    def open_marks_entry(self, exam_id, popup2):
        popup2.dismiss()
        app = App.get_running_app()
        app.selected_exam_id = exam_id
        self.manager.current = 'marks_entry'

    def view_student(self, std_id):
        app = App.get_running_app()
        app.selected_student_id = std_id
        self.manager.current = 'student_detail'


class AddStudentScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        self.ids.class_input.text = app.selected_class
        # Clear fields
        self.ids.name_input.text = ""
        self.ids.father_name_input.text = ""
        self.ids.mother_name_input.text = ""
        self.ids.father_mobile_input.text = ""
        self.ids.alt_mobile_input.text = ""
        self.ids.section_input.text = ""

    def save_student(self):
        name = self.ids.name_input.text.strip()
        f_name = self.ids.father_name_input.text.strip()
        m_name = self.ids.mother_name_input.text.strip()
        f_mob = self.ids.father_mobile_input.text.strip()
        a_mob = self.ids.alt_mobile_input.text.strip()
        cls = self.ids.class_input.text.strip()
        sec = self.ids.section_input.text.strip()

        if not name or not f_mob:
            show_popup("Error", "Name and Father's Mobile are required!")
            return

        std_id = db.add_student(name, f_name, m_name, f_mob, a_mob, cls, sec)
        show_popup("Success", f"Student Added Successfully!\nID: {std_id}")
        self.go_back()

    def go_back(self):
        self.manager.current = 'class_management'


class StudentDetailScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        std_id = app.selected_student_id
        student = db.get_student_by_id(std_id)
        if not student:
            return

        # Personal details
        grid = self.ids.personal_details_grid
        grid.clear_widgets()
        grid.add_widget(Label(text="Name:"))
        grid.add_widget(Label(text=student[2]))
        grid.add_widget(Label(text="ID:"))
        grid.add_widget(Label(text=student[1]))
        grid.add_widget(Label(text="Father's Name:"))
        grid.add_widget(Label(text=student[3] or ""))
        grid.add_widget(Label(text="Mobile:"))
        grid.add_widget(Label(text=student[5] or ""))
        grid.add_widget(Label(text="Class:"))
        grid.add_widget(Label(text=student[7]))
        
        # Exam Summary
        tot, att, msd = db.get_student_exam_stats(std_id, student[7])
        egrid = self.ids.exam_summary_grid
        egrid.clear_widgets()
        egrid.add_widget(Label(text="Total Exams:"))
        egrid.add_widget(Label(text=str(tot)))
        egrid.add_widget(Label(text="Attended:"))
        egrid.add_widget(Label(text=str(att)))
        egrid.add_widget(Label(text="Missed:"))
        egrid.add_widget(Label(text=str(msd)))

        # Recent exams
        elist = self.ids.exam_list_grid
        elist.clear_widgets()
        marks = db.get_marks_for_student(std_id)
        for m in marks:
            # m: exam_name, total_marks, obtained_marks, exam_date, class_name
            text = f"{m[0]}: {m[2]}/{m[1]} ({m[3]})"
            elist.add_widget(Label(text=text, size_hint_y=None, height=dp(30)))

        # Payments
        plist = self.ids.payment_list_grid
        plist.clear_widgets()
        payments = db.get_payments_for_student(std_id)
        for p in payments:
            # p: id, std_id, class, month, year, amount, status
            text = f"{p[3]} {p[4]} - {p[6].upper()} (Amt: {p[5]})"
            col = (0.2, 0.8, 0.2, 1) if p[6] == 'paid' else (0.8, 0.2, 0.2, 1)
            lbl = Label(text=text, size_hint_y=None, height=dp(30), color=col)
            plist.add_widget(lbl)

        # Promotion History
        phlist = self.ids.promotion_list_grid
        phlist.clear_widgets()
        history = db.get_promotion_history(std_id)
        for h in history:
            text = f"{h[4]}: {h[2]} -> {h[3]} | Summary: {h[5]}"
            phlist.add_widget(Label(text=text, size_hint_y=None, height=dp(30)))

    def go_back(self):
        # We need to detect if coming from search or class management
        # For simplicity, just return to dashboard to be safe, or batch list if selected_class exists
        self.manager.current = 'class_management'

    def edit_student(self):
        self.manager.current = 'edit_student'

    def delete_student(self):
        app = App.get_running_app()
        db.delete_student(app.selected_student_id)
        show_popup("Deleted", "Student record successfully deleted.")
        self.go_back()


class AddExamScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        self.ids.class_label.text = f"Class: {app.selected_class}"
        self.ids.exam_name_input.text = ""
        self.ids.total_marks_input.text = ""
        from datetime import datetime
        self.ids.exam_date_input.text = datetime.now().strftime("%Y-%m-%d")

    def save_exam(self):
        app = App.get_running_app()
        name = self.ids.exam_name_input.text.strip()
        marks = self.ids.total_marks_input.text.strip()
        date = self.ids.exam_date_input.text.strip()

        if not name or not marks or not date:
            show_popup("Error", "All fields are required!")
            return

        exam_id = db.add_exam(app.selected_class, name, float(marks), date)
        app.selected_exam_id = exam_id
        self.manager.current = 'marks_entry'

    def go_back(self):
        self.manager.current = 'class_management'


class MarksEntryScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        exam_id = app.selected_exam_id
        db.cursor.execute("SELECT exam_name, class_name FROM Exams WHERE exam_id = ?", (exam_id,))
        exam = db.cursor.fetchone()
        if not exam:
            return
        
        self.ids.title_label.text = f"{exam[1]} - {exam[0]}"
        
        # Load students
        self.student_inputs = {}
        grid = self.ids.students_marks_list
        grid.clear_widgets()
        
        students = db.get_marks_by_exam(exam_id)
        for s in students:
            # s: id, name, obtained_marks
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=5)
            row.add_widget(Label(text=s[0], size_hint_x=0.25))
            row.add_widget(Label(text=s[1], size_hint_x=0.4))
            
            inp = TextInput(text=str(s[2]) if s[2] is not None else "", multiline=False, input_filter='float', size_hint_x=0.35)
            self.student_inputs[s[0]] = inp
            row.add_widget(inp)
            grid.add_widget(row)

    def save_all_marks(self):
        app = App.get_running_app()
        exam_id = app.selected_exam_id
        for std_id, inp in self.student_inputs.items():
            if inp.text.strip():
                try:
                    marks = float(inp.text.strip())
                    db.add_or_update_mark(std_id, exam_id, marks)
                except ValueError:
                    pass
        show_popup("Success", "Marks saved successfully.")

    def generate_pdf(self):
        self.save_all_marks() # save first
        app = App.get_running_app()
        filepath = generate_exam_result_pdf(app.selected_exam_id, db)
        if filepath:
            show_popup("PDF Generated", f"Saved successfully at:\n{filepath}")
        else:
            show_popup("Error", "Could not generate PDF.")
            
    def go_back(self):
        self.manager.current = 'class_management'


class PaymentScreen(Screen):
    def search_student(self):
        q = self.ids.search_input.text.strip()
        student = db.get_student_by_id(q)
        if student:
            self.current_student = student
            self.ids.student_info_label.text = f"Selected: {student[2]} ({student[1]}) - Class: {student[7]}"
            self.ids.amount_input.text = str(db.get_class_fee(student[7]))
            self.load_history()
        else:
            from datetime import datetime
            self.current_student = None
            self.ids.student_info_label.text = "Student not found."

    def mark_paid(self):
        if not hasattr(self, 'current_student') or not self.current_student:
            show_popup("Error", "No student selected.")
            return
            
        month = self.ids.month_spinner.text
        if month == 'Select Month':
            show_popup("Error", "Please select a month.")
            return
            
        amount = self.ids.amount_input.text.strip()
        if not amount:
            show_popup("Error", "Please enter amount.")
            return
        
        from datetime import datetime
        year = str(datetime.now().year)
        
        db.add_payment(self.current_student[1], self.current_student[7], month, year, float(amount), 'paid')
        show_popup("Success", "Payment recorded successfully.")
        self.load_history()

    def load_history(self):
        if not hasattr(self, 'current_student') or not self.current_student:
            return
        grid = self.ids.payment_history_list
        grid.clear_widgets()
        payments = db.get_payments_for_student(self.current_student[1])
        for p in payments:
            col = (0.2, 0.8, 0.2, 1) if p[6] == 'paid' else (0.8, 0.2, 0.2, 1)
            row = BoxLayout(size_hint_y=None, height=dp(30))
            row.add_widget(Label(text=f"{p[3]} {p[4]}", color=col))
            row.add_widget(Label(text=f"Amount: {p[5]}", color=col))
            row.add_widget(Label(text=p[6].upper(), color=col))
            grid.add_widget(row)


class PromotionScreen(Screen):
    def promote_class(self):
        old_class = self.ids.old_class_spinner.text
        new_class = self.ids.new_class_spinner.text
        
        students = db.get_students_by_class(old_class)
        if not students:
            show_popup("Info", f"No active students found in {old_class}.")
            return
            
        for s in students:
            db.promote_student(s[1], new_class, f"Promoted from {old_class} to {new_class}")
            
        show_popup("Success", f"Promoted {len(students)} students from {old_class} to {new_class}.")


class SearchScreen(Screen):
    def perform_search(self):
        q = self.ids.search_input.text.strip()
        student = db.get_student_by_id(q)
        if not student:
            self.ids.status_label.text = "Student not found!"
            self.ids.search_results_container.clear_widgets()
            return
        
        self.ids.status_label.text = ""
        app = App.get_running_app()
        app.selected_student_id = student[1]
        self.manager.current = 'student_detail'


class SettingsScreen(Screen):
    def on_enter(self):
        self.inputs = {}
        grid = self.ids.fee_grid
        grid.clear_widgets()
        
        classes = db.get_classes()
        for c in classes:
            grid.add_widget(Label(text=c[1]))
            grid.add_widget(Label(text="Monthly Fee:"))
            inp = TextInput(text=str(c[2]), multiline=False, input_filter='float')
            self.inputs[c[1]] = inp
            grid.add_widget(inp)

    def save_fees(self):
        for class_name, inp in self.inputs.items():
            if inp.text.strip():
                db.update_class_fee(class_name, float(inp.text.strip()))
        show_popup("Success", "Class fees updated successfully.")

    def update_password(self):
        new_pwd = self.ids.new_password_input.text.strip()
        if len(new_pwd) >= 4:
            db.update_admin_password(new_pwd)
            self.ids.new_password_input.text = ""
            show_popup("Success", "Admin password updated successfully.")
        else:
            show_popup("Error", "Password must be at least 4 characters long.")


class EditStudentScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        std_id = app.selected_student_id
        student = db.get_student_by_id(std_id)
        if not student:
            return
            
        self.ids.name_input.text = student[2]
        self.ids.father_name_input.text = student[3] or ""
        self.ids.mother_name_input.text = student[4] or ""
        self.ids.father_mobile_input.text = student[5] or ""
        self.ids.alt_mobile_input.text = student[6] or ""
        self.ids.class_input.text = student[7]
        self.ids.section_input.text = student[8] or ""

    def update_student(self):
        app = App.get_running_app()
        std_id = app.selected_student_id
        name = self.ids.name_input.text.strip()
        f_name = self.ids.father_name_input.text.strip()
        m_name = self.ids.mother_name_input.text.strip()
        f_mob = self.ids.father_mobile_input.text.strip()
        a_mob = self.ids.alt_mobile_input.text.strip()
        cls = self.ids.class_input.text.strip()
        sec = self.ids.section_input.text.strip()

        if not name or not f_mob:
            show_popup("Error", "Name and Father's Mobile are required!")
            return

        db.update_student(std_id, name, f_name, m_name, f_mob, a_mob, cls, sec)
        show_popup("Success", "Student updated successfully!")
        self.go_back()

    def go_back(self):
        self.manager.current = 'student_detail'


class ReportsScreen(Screen):
    def on_enter(self):
        self.ids.total_students_label.text = str(db.get_total_students())
        self.ids.total_batches_label.text = str(db.get_total_batches())
        self.ids.total_exams_label.text = str(db.get_total_exams())
        self.ids.total_revenue_label.text = f"${db.get_total_revenue():.2f}"
        self.ids.total_payments_label.text = str(db.get_total_payments())


class CoachingManagerApp(App):
    # App-level globals for passing data between screens
    selected_class = None
    selected_student_id = None
    selected_exam_id = None

    def build(self):
        # Load all KV files mapped earlier
        kv_path = './kv/'
        if os.path.exists(kv_path):
            for kv_file in os.listdir(kv_path):
                if kv_file.endswith('.kv'):
                    Builder.load_file(os.path.join(kv_path, kv_file))

        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(BatchListScreen(name='batch_list'))
        sm.add_widget(ClassManagementScreen(name='class_management'))
        sm.add_widget(AddStudentScreen(name='add_student'))
        sm.add_widget(StudentDetailScreen(name='student_detail'))
        sm.add_widget(AddExamScreen(name='add_exam'))
        sm.add_widget(MarksEntryScreen(name='marks_entry'))
        sm.add_widget(PaymentScreen(name='payment'))
        sm.add_widget(PromotionScreen(name='promotion'))
        sm.add_widget(SearchScreen(name='search'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(EditStudentScreen(name='edit_student'))
        sm.add_widget(ReportsScreen(name='reports'))

        return sm


if __name__ == '__main__':
    CoachingManagerApp().run()
