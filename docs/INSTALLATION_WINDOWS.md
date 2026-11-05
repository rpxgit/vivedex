# Vivédex — Windows Installation and Operations Guide

This document describes how to install, configure, verify, and operate Vivédex on Microsoft Windows.

Writing standard: ASD-STE100 (Simplified Technical English).

---

## 1. System Requirements

Ensure that your Windows workstation meets these minimum requirements:

| Component | Minimum Specification | Recommended Specification |
|---|---|---|
| Operating System | Windows 10 64-bit (Build 19041+) | Windows 11 64-bit |
| Python Environment | Python 3.10 64-bit | Python 3.11 or Python 3.14 64-bit |
| Command Shell | Windows PowerShell 5.1 | PowerShell 7+ |
| Web Browser | Google Chrome, Edge, or Firefox | Latest Google Chrome or Edge |
| Memory (RAM) | 4 GB | 8 GB or more |
| Storage | 500 MB free space | 2 GB free space |
| Internet Connection | Required for initial setup and GBIF lookup | High-speed broadband |

---

## 2. Quick Start: One-Click Launch

1. Clone or download the Vivédex repository to a local folder (for example, `C:\Users\<Username>\Projects\vivedex`).
2. Double-click `Launch-Vivedex.bat` in the root folder.
3. The launcher executes the following automated steps:
   - Verifies the Python installation.
   - Creates a local virtual environment (`.venv`) if one does not exist.
   - Installs required packages from `requirements.txt`.
   - Initializes database schemas safely without data loss.
   - Starts the Streamlit server at `http://localhost:8501`.
   - Opens the platform in your default web browser.

---

## 3. Manual Installation and Setup via PowerShell

If you prefer using the PowerShell command prompt, follow these steps:

### Step 3.1: Open PowerShell
Open Windows PowerShell and navigate to the project directory:
```powershell
cd C:\Users\<Username>\Projects\vivedex
```

### Step 3.2: Initialize the Environment
Run the initializer script:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\Initialize-Vivedex.ps1
```
This script:
- Finds Python on your system (checking `py -3`, `python`, and default paths).
- Creates `.venv` if not already present.
- Installs dependencies: `streamlit`, `pydantic`, `pillow`, `httpx`, `pytest`.
- Verifies that `data/vivedex.db` schema tables exist.

### Step 3.3: Run Diagnostic Pre-Flight Check
Verify your environment before launching:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\Check-Vivedex.ps1
```
Expected output:
```text
[OK] Virtual environment found: .venv\Scripts\python.exe
[OK] Detected Python Version: Python 3.14.7
  [OK] Module 'streamlit' is available.
  [OK] Module 'pydantic' is available.
  [OK] Module 'PIL' is available.
  [OK] Module 'httpx' is available.
  [OK] Module 'pytest' is available.
[OK] Database found: ...\data\vivedex.db
[SUCCESS] All pre-flight checks passed.
```

### Step 3.4: Start the Application
Start the server:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\Start-Vivedex.ps1
```
To launch without opening a browser window or to select an alternative port:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\Start-Vivedex.ps1 -Port 8502 -NoBrowser
```

---

## 4. Administrator Provisioning

Vivédex does not create an administrator account automatically. This design protects the security perimeter.

To provision the first administrator account, execute the CLI tool using `.venv`:
```powershell
.\.venv\Scripts\python.exe -m src.cli create-admin --username admin --password "StrongPassw0rd!" --display-name "System Administrator"
```

To verify whether an administrator exists:
```powershell
.\.venv\Scripts\python.exe -m src.cli check-admin
```

---

## 5. AI Vision Configuration (Bring Your Own Key)

Vivédex supports multimodal vision identification using the Meta Model API (Muse Spark / Llama 3.2 Vision).

You have two methods to configure your API key:

### Method A: User Account Settings (Recommended / Session Isolated)
1. Register and log in through the sidebar.
2. Navigate to **Account Settings** (`http://localhost:8501/settings`).
3. Under **AI Provider Settings**, paste your Meta Model API key.
4. Click **Test & Connect Meta Model API**.
5. Your key is stored in your active session state and is never saved to the SQLite database.

### Method B: Environment Variable (Global Fallback)
Create a `.env` file in the project root:
```env
MODEL_API_KEY=your_meta_model_api_key_here
```

---

## 6. Data Storage and Persistence

- **Database:** SQLite database located at `data/vivedex.db`.
- **Uploaded Images:** Stored under `data/uploads/`.
- **Schema Management:** Handled via `src/database.py` with `CREATE TABLE IF NOT EXISTS`. Existing tables, user profiles, field sightings, and collections are preserved during updates.

---

## 7. Troubleshooting

### Issue: PowerShell Script Execution Policy Restriction
If PowerShell reports: `File ... cannot be loaded because running scripts is disabled on this system`:
**Resolution:** Launch using `-ExecutionPolicy Bypass`:
```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\Start-Vivedex.ps1
```

### Issue: Port 8501 Conflict
If port 8501 is occupied by another application:
**Resolution:** Specify an alternate port:
```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\Start-Vivedex.ps1 -Port 8502
```

### Issue: Python Not Recognized
If Python is not detected:
**Resolution:** Download and install Python 3.10+ from [python.org](https://www.python.org). Ensure you check **"Add Python to PATH"** during installation.
