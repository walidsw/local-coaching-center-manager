# Local Coaching Center Manager

A fully offline coaching center management application built with Python, Kivy, SQLite, and ReportLab. It supports student management, exams, PDF result generation, payments, and promotion history.

## Folder Structure
```text
.
├── main.py              # Main application logic & UI routing
├── database.py          # SQLite schema and CRUD operations
├── pdf_generator.py     # PDF generation logic using ReportLab
├── kv/                  # Kivy UI layout files
│   ├── login.kv
│   ├── dashboard.kv
│   ├── batch_list.kv
│   ├── class_management.kv
│   ├── add_student.kv
│   ├── student_detail.kv
│   ├── exam.kv
│   ├── marks.kv
│   ├── payment.kv
│   ├── promotion.kv
│   ├── search.kv
│   └── settings.kv
└── output/              # Folder where generated PDFs are saved
```

## Running the App on Desktop (Windows/Mac/Linux)

1. Ensure you have Python 3 installed.
2. Install the required dependencies:
   ```bash
   pip install kivy reportlab
   ```
3. Run the application:
   ```bash
   python main.py
   ```

*Note: The default admin credentials are `admin` / `admin` for testing.*

## Building the Android APK using Buildozer

Buildozer is a tool natively supported on Linux/macOS that packages your Python app into an Android APK.

1. Install Buildozer:
   ```bash
   pip install buildozer
   ```

2. Initialize Buildozer in the project directory:
   ```bash
   buildozer init
   ```
   This will create a `buildozer.spec` file.

3. Edit the `buildozer.spec` file:
   - Change `title` to `Local Coaching Center Manager`
   - Change `package.name` to `coachingmanager`
   - Change `package.domain` to `org.yourdomain`
   - Ensure the `requirements` line looks like this:
     ```ini
     requirements = python3,kivy==2.3.0,reportlab
     ```
   - Make sure `sqlite3` is supported natively by Python, so no need to specify it explicitly, but reportlab needs to be added.
   - Adjust `android.permissions` to include storage permissions if needed for saving PDFs:
     ```ini
     android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
     ```
   
4. Connect your Android device via USB and enable USB Debugging, or just build the generic APK:
   ```bash
   buildozer android debug
   ```
   Or to compile and deploy automatically to connected device:
   ```bash
   buildozer android debug deploy run
   ```

5. Once built, the `.apk` file will be generated inside the `bin/` directory.

### Important Notes for Android:
- By default, Kivy on Android uses a confined private storage. To view the generated PDFs easily from outside the app, you may need to save it to public storage (e.g., `/sdcard/Download/`) dynamically in `main.py`/`pdf_generator.py` using `android` library from `jnius`. For now, it saves to `./output` relative to the current working directory.
