# Nozama AI Shopping Assistant Setup

This guide sets up the CSAF Demo Project locally on Windows, Linux, or macOS.

The project is an educational React and FastAPI application. It uses a local SQLite database and a deterministic mock AI provider by default. No cloud account or API key is required for the standard demo.

## 1. Project Layout

The repository contains two applications that run at the same time:

- `backend/`: Python FastAPI API, SQLite persistence, agent providers, security policies, and tests.
- `frontend/`: React and TypeScript single-page application served by Vite.
- `docs/`: Architecture, demonstration, and student-work documentation.
- `.env.example`: Example runtime configuration.

You need one terminal for the backend and a second terminal for the frontend.

## 2. Required Tools

### 2.1 Git

Git is useful for downloading the repository and managing changes.

- Download: <https://git-scm.com/downloads>
- Verify the installation:

Windows PowerShell:

```powershell
git --version
```

Linux:

```bash
git --version
```

macOS:

```bash
git --version
```

If the project is already present on your computer, Git is optional for running it.

### 2.2 Python 3.11 or newer

Python runs the FastAPI backend. Python 3.11 or newer is recommended.

- Download: <https://www.python.org/downloads/>
- Python documentation: <https://docs.python.org/3/>

Install on Windows with either the official installer or Windows Package Manager:

```powershell
winget install Python.Python.3.12
```

Install on Ubuntu/Debian Linux:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

Install on macOS with Homebrew:

```bash
brew install python@3.12
```

Verify Python and pip. The `python` command differs on some systems, so use the command that works on your machine:

Windows PowerShell:

```powershell
py --version
py -m pip --version
```

Linux:

```bash
python3 --version
python3 -m pip --version
```

macOS:

```bash
python3 --version
python3 -m pip --version
```

On Windows, enable **Add python.exe to PATH** when using the official installer. If `py` is unavailable, use `python` in the commands below.

### 2.3 Node.js and npm

Node.js runs the frontend development server and npm installs the frontend packages.

- Download: <https://nodejs.org/en/download>
- Node.js documentation: <https://nodejs.org/docs/latest/api/>
- npm documentation: <https://docs.npmjs.com/>

Use the current Node.js LTS release. npm is included with Node.js.

Install on Windows with Windows Package Manager:

```powershell
winget install OpenJS.NodeJS.LTS
```

Install on Ubuntu/Debian Linux using the NodeSource LTS setup:

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
```

Install on macOS with Homebrew:

```bash
brew install node
```

Verify Node.js and npm:

Windows PowerShell:

```powershell
node --version
npm --version
```

Linux:

```bash
node --version
npm --version
```

macOS:

```bash
node --version
npm --version
```

### 2.4 No database server or Docker is required

The backend uses SQLite, which is included through Python's SQLite support and creates `backend/nozama.db` on first startup. Docker, PostgreSQL, and a separate database server are not needed.

## 3. Download or Open the Project

If you already have the project folder, open a terminal in its root directory:

```text
CSAF_Demo_Project/
```

If you need to clone it, replace `<repository-url>` with the repository URL.

Windows PowerShell:

```powershell
git clone <repository-url>
Set-Location CSAF_Demo_Project
```

Linux:

```bash
git clone <repository-url>
cd CSAF_Demo_Project
```

macOS:

```bash
git clone <repository-url>
cd CSAF_Demo_Project
```

Confirm that the root contains `backend`, `frontend`, `README.md`, and `.env.example`.

Windows PowerShell:

```powershell
Get-ChildItem
```

Linux:

```bash
ls
```

macOS:

```bash
ls
```

## 4. Configure Environment Variables

The application works in mock mode without a Gemini key. Copy `.env.example` to `.env` in the project root. The backend also accepts `.env` inside `backend/`.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Windows Command Prompt:

```bat
copy .env.example .env
```

Linux:

```bash
cp .env.example .env
```

macOS:

```bash
cp .env.example .env
```

The default configuration is equivalent to:

```dotenv
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
AGENT_PROVIDER=mock
DATABASE_URL=sqlite:///./nozama.db
```

### Mock mode

Use this for the normal classroom or fair demonstration:

```dotenv
AGENT_PROVIDER=mock
GEMINI_API_KEY=
```

Mock mode is deterministic, does not call the internet, and does not need an API key.

### Optional Gemini mode

Gemini mode requires a Google AI API key.

- Google AI Studio: <https://aistudio.google.com/app/apikey>
- Google GenAI Python SDK: <https://googleapis.github.io/python-genai/>

Put the key only in the backend-readable `.env` file:

```dotenv
AGENT_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-2.0-flash
```

Do not put the key in frontend files or variables beginning with `VITE_`; Vite exposes those values to the browser bundle. Never commit `.env` or share the key in logs.

## 5. Install Backend Packages

The backend uses a Python virtual environment so its packages do not alter the system Python installation.

### 5.1 Create the virtual environment

Run these commands from the project root.

Windows PowerShell:

```powershell
Set-Location backend
py -m venv .venv
```

Windows Command Prompt:

```bat
cd backend
py -m venv .venv
```

Linux:

```bash
cd backend
python3 -m venv .venv
```

macOS:

```bash
cd backend
python3 -m venv .venv
```

### 5.2 Activate the virtual environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
.venv\Scripts\activate.bat
```

Linux:

```bash
source .venv/bin/activate
```

macOS:

```bash
source .venv/bin/activate
```

After activation, the terminal prompt normally begins with `(.venv)`. If PowerShell blocks activation, run PowerShell as the current user and retry:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 5.3 Upgrade packaging tools and install dependencies

Windows PowerShell or Command Prompt:

```powershell
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

Linux:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

macOS:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

When the virtual environment is active, `python -m pip` is also valid on all three platforms:

```text
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5.4 Backend package inventory

The versions are controlled by `backend/requirements.txt`.

| Package             | Purpose                                                    | Documentation                                                  |
| ------------------- | ---------------------------------------------------------- | -------------------------------------------------------------- |
| `fastapi`           | Web framework and API route handling                       | <https://fastapi.tiangolo.com/>                                |
| `uvicorn[standard]` | ASGI server that runs FastAPI locally                      | <https://www.uvicorn.org/>                                     |
| `pydantic`          | Request, response, and tool-argument validation            | <https://docs.pydantic.dev/>                                   |
| `pydantic-settings` | Loads typed settings from environment variables and `.env` | <https://docs.pydantic.dev/latest/concepts/pydantic_settings/> |
| `sqlalchemy`        | Database engine and ORM models                             | <https://docs.sqlalchemy.org/>                                 |
| `python-dotenv`     | `.env` file support used by the settings stack             | <https://pypi.org/project/python-dotenv/>                      |
| `google-genai`      | Optional Google Gemini provider                            | <https://googleapis.github.io/python-genai/>                   |
| `httpx`             | HTTP client used by the application and tests              | <https://www.python-httpx.org/>                                |
| `pytest`            | Backend test runner                                        | <https://docs.pytest.org/>                                     |
| `python-multipart`  | Multipart form parsing support for FastAPI                 | <https://pypi.org/project/python-multipart/>                   |

## 6. Install Frontend Packages

Open a second terminal and return to the project root before installing frontend packages.

Windows PowerShell:

```powershell
Set-Location ..
Set-Location frontend
npm install
```

Windows Command Prompt:

```bat
cd ..
cd frontend
npm install
```

Linux:

```bash
cd ../frontend
npm install
```

macOS:

```bash
cd ../frontend
npm install
```

`npm install` uses `frontend/package-lock.json` to install the locked dependency tree and creates `frontend/node_modules/`.

### Frontend package inventory

| Package                | Type        | Purpose                                                                        | Documentation                                    |
| ---------------------- | ----------- | ------------------------------------------------------------------------------ | ------------------------------------------------ |
| `react`                | Runtime     | Component-based UI framework                                                   | <https://react.dev/>                             |
| `react-dom`            | Runtime     | Renders React into the browser DOM                                             | <https://react.dev/reference/react-dom>          |
| `react-router-dom`     | Runtime     | Client-side routes for shop, cart, checkout, X-Ray, control, and monitor pages | <https://reactrouter.com/>                       |
| `typescript`           | Development | Static type checking for frontend code                                         | <https://www.typescriptlang.org/docs/>           |
| `vite`                 | Development | Frontend dev server and production bundler                                     | <https://vite.dev/guide/>                        |
| `@vitejs/plugin-react` | Development | React integration for Vite                                                     | <https://github.com/vitejs/vite-plugin-react>    |
| `@types/react`         | Development | TypeScript declarations for React                                              | <https://www.npmjs.com/package/@types/react>     |
| `@types/react-dom`     | Development | TypeScript declarations for React DOM                                          | <https://www.npmjs.com/package/@types/react-dom> |

The project intentionally uses plain CSS and the browser Fetch API. It does not require Tailwind, a UI component library, Redux, or another frontend data library.

## 7. Run the Application

### 7.1 Start the backend

Use the terminal where the backend virtual environment is active and the current directory is `backend/`.

Windows PowerShell or Command Prompt:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Linux:

```bash
python3 -m uvicorn app.main:app --reload --port 8000
```

macOS:

```bash
python3 -m uvicorn app.main:app --reload --port 8000
```

If the virtual environment is active, `python` resolves to the virtual-environment interpreter. The backend will:

1. Create the SQLite database at `backend/nozama.db`.
2. Create database tables.
3. Insert or update the demo seed data.
4. Listen on `http://127.0.0.1:8000`.

Useful backend URLs:

- Health check: <http://127.0.0.1:8000/api/health>
- Interactive API docs: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

Leave this terminal running.

### 7.2 Start the frontend

Use the second terminal from `frontend/`.

Windows PowerShell or Command Prompt:

```powershell
npm run dev
```

Linux:

```bash
npm run dev
```

macOS:

```bash
npm run dev
```

Open the URL printed by Vite, normally <http://127.0.0.1:5173>. The frontend proxies `/api` requests to the backend at port 8000.

Leave this terminal running as well.

### 7.3 Stop the application

In each running terminal, press `Ctrl+C`.

Windows PowerShell:

```powershell
# Press Ctrl+C in the backend and frontend terminals
```

Linux:

```bash
# Press Ctrl+C in the backend and frontend terminals
```

macOS:

```bash
# Press Ctrl+C in the backend and frontend terminals
```

## 8. Run Tests and Production Build

### Backend tests

From `backend/` with the virtual environment active:

Windows PowerShell or Command Prompt:

```powershell
python -m pytest
```

Linux:

```bash
python3 -m pytest
```

macOS:

```bash
python3 -m pytest
```

The backend test configuration is in `backend/pytest.ini`.

### Frontend type-check and build

From `frontend/`:

Windows PowerShell or Command Prompt:

```powershell
npm run build
```

Linux:

```bash
npm run build
```

macOS:

```bash
npm run build
```

This runs TypeScript checking followed by a Vite production build. The generated `frontend/dist/` directory is build output and does not need to be committed.

### Preview the production frontend build

After `npm run build`, from `frontend/`:

Windows PowerShell or Command Prompt:

```powershell
npm run preview
```

Linux:

```bash
npm run preview
```

macOS:

```bash
npm run preview
```

The preview server normally uses port 4173. The backend CORS configuration already allows the local preview origins.

## 9. Demonstration Flow

1. Open the frontend at `http://127.0.0.1:5173`.
2. Use **Reset Demo** if the database has state from an earlier run.
3. Choose **vulnerable** mode and load the demo request to show the attack succeeding.
4. Reset the demo, choose **patched** mode, and submit the same request to show the attack being blocked.
5. Use the X-Ray, Control, and Monitor pages to inspect hidden listing content, policy settings, and activity events.

The transaction is simulated. No real product, payment, customer profile, or purchase is used.

## 10. Common Problems

### `python` or `py` is not recognized

Install Python from <https://www.python.org/downloads/> and enable PATH integration. On Linux or macOS, use `python3`.

### `venv` creation fails on Linux

Install the platform package and retry:

```bash
sudo apt update
sudo apt install -y python3-venv
```

### PowerShell refuses to activate `.venv`

Run this once for your Windows user, then activate again:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### `npm` is not recognized

Install the Node.js LTS release from <https://nodejs.org/en/download> and open a new terminal.

### Port 8000 or 5173 is already in use

Stop the process using the port, or use a different backend port and update the Vite proxy.

Backend on another port:

Windows PowerShell:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

Linux:

```bash
python3 -m uvicorn app.main:app --reload --port 8001
```

macOS:

```bash
python3 -m uvicorn app.main:app --reload --port 8001
```

Then change `frontend/vite.config.ts` from `http://127.0.0.1:8000` to `http://127.0.0.1:8001` and restart Vite. The backend CORS list may also need the new frontend origin if the frontend port changes.

### The frontend loads but API calls fail

Check all of the following:

- The backend terminal is still running.
- The backend health URL returns `{"ok": true, "service": "nozama-backend"}`.
- The frontend was started from `frontend/`.
- The Vite proxy still points to `http://127.0.0.1:8000`.
- The backend and frontend ports are not blocked by another process.

### Gemini does not run

Confirm that `GEMINI_API_KEY` is set in the root `.env` or `backend/.env`, that `AGENT_PROVIDER=gemini`, and that the key is valid. Missing or invalid configuration falls back to mock mode; mock mode is the supported offline demo path.

## 11. Useful References

- Project overview: `README.md`
- Architecture: `docs/ARCHITECTURE.md`
- Demo instructions: `docs/DEMO_GUIDE.md`
- Student tasks: `docs/STUDENT_WORK.md`
- Backend details: `backend/README.md`
- Frontend details: `frontend/README.md`
