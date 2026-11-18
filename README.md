# KNOWRA

A modular adaptive learning platform built with a **React + Vite** frontend and a **FastAPI** backend.

## 📂 Project Structure
```
KNOWRA/
├─ .gitignore
├─ README.md
├─ frontend/                # React + Vite app
│   ├─ index.html
│   ├─ package.json
│   ├─ vite.config.js
│   ├─ tailwind.config.cjs
│   └─ src/
│       ├─ main.jsx
│       └─ App.jsx
├─ backend/                 # FastAPI service
│   ├─ venv/                # Python virtual environment (create locally)
│   ├─ requirements.txt
│   ├─ .env                 # Environment variables (fill in)
│   └─ app/
│       ├─ __init__.py
│       ├─ main.py          # FastAPI entry point
│       ├─ api/
│           └─ health.py   # Health endpoint
│       └─ cognitive_engine/   # Placeholder for future modules
│           ├─ __init__.py
│           └─ engine.py      # Stub
│       └─ data/
│           ├─ math_concepts/
│           │   └─ README.md
│           └─ questions/
│               └─ README.md
├─ research/               # Research notes, papers, etc.
│   └─ README.md
└─ docs/                   # Project documentation
    └─ README.md
```

## 🛠️ Prerequisites (Windows)
- **Node.js** (>= 20) – includes `npm`.
- **Python** (>= 3.11).
- **Git** (already present).

## 🚀 Setup
### 1. Clone the repo (if not already)
```powershell
git clone https://github.com/annibell17/KNOWRA.git
cd KNOWRA
```
### 2. Frontend
```powershell
# Make sure npm is usable – you may need to allow script execution:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# Install dependencies
npm install

# Run development server
npm run dev   # opens http://localhost:3000

# Build for production
npm run build
```
### 3. Backend
```powershell
# Create a virtual environment (run from the repository root)
python -m venv backend\venv

# Activate it
backend\venv\Scripts\Activate.ps1   # PowerShell
# or
backend\venv\Scripts\activate.bat   # Command Prompt

# Install Python dependencies
pip install -r backend\requirements.txt

# Load environment variables (edit .env first if needed)
$Env:FASTAPI_ENV = "development"

# Run the FastAPI server
uvicorn backend.app.main:app --reload --port 8000
```
The health endpoint is available at `http://127.0.0.1:8000/health` and should return `{"status":"ok"}`.

### 4. Database
SQLite is used by default. The file will be created automatically at runtime (e.g., `backend/app/database.db`). No extra setup required.

## 📚 Next steps
- Implement the **cognitive engine** inside `backend/app/cognitive_engine/`.
- Populate `backend/app/data/math_concepts` and `backend/app/data/questions` with real data.
- Extend the React UI with routes, authentication, etc.

---
*This scaffold provides a clean, scalable base. All commands are safe – they only create files/directories and install packages locally.*