Aroven — Centralized Medical & Healthcare Management Platform
A unified healthcare operations platform designed to bridge clinical workflows, e-pharmacy retail, and patient record management. The platform delivers secure role-based access, decoupled backend service layers, integrated prescription handling, and direct database persistence.

Highlights & Features
Patient & Clinical Care Portal: Manage patient profiles, consultations, complete medical histories, and digital prescription assignments.

Store Commerce & E-Pharmacy: Integrated catalog browsing, shopping cart workflows, automated checkout/payments, and recurring healthcare subscription services.

Granular Identity & Access Control: Secure authentication endpoints, token/session handlers, and role-based access for patients, doctors, and platform administrators.

High-Throughput Backend: Built on asynchronous Python (FastAPI) paired with structured domain modeling and connection-pooled SQL sessions.

Responsive Frontend Client: Modular React application handling route transitions, global state management, and unified portal views.

System Architecture

[ Platform User ]
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Web Application (React)                 │
│  App.jsx ──┬── Patient Dashboard & Medical History          │
│            ├── Shopping Cart & Product Catalog              │
│            ├── Prescription Portal                          │
│            └── Sign-in / Sign-up (Auth.jsx) & State Mgmt    │
└──────────────────────────────┬──────────────────────────────┘
                               │ API Requests / Dispatches
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend Services (FastAPI)                │
│                                                             │
│  [ Store Commerce ]          [ Care Services ]              │
│  • Payments (payment.py)     • Patient Services             │
│  • Medical Store             • Medical History Records      │
│  • Cart Services             • Doctor Management            │
│  • Subscriptions                                            │
│                                                             │
│  [ Identity & Access ]       [ API & Persistence Engine ]   │
│  • Auth Routes & Handlers    • FastAPI Core (main.py)       │
│                              • Domain Models (models.py)    │
│                              • DB Sessions (database.py)    │
└──────────────────────────────┬──────────────────────────────┘
                               │ Queries & Transactions
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                         SQL Database                        │
└─────────────────────────────────────────────────────────────┘

Tech Stack
Frontend: React.js, Context API / Redux, Axios, Modern CSS

Backend: Python 3.10+, FastAPI, Pydantic, SQLAlchemy / ORM

Database: Microsoft SQL Server / Relational SQL

Tools & Environment: Docker, Nginx, Git

Directory Structure
Plaintext
├── client/                     # React frontend source
│   ├── public/                 # Static assets
│   └── src/
│       ├── components/         # Reusable UI modules (CartView, ProductList, etc.)
│       ├── views/              # Core pages (Dashboard, Prescription Portal, History)
│       ├── App.jsx             # Top-level routing
│       └── Auth.jsx            # Authentication interface
│
├── server/                     # FastAPI backend source
│   ├── app/
│   │   ├── routers/            # Domain route controllers
│   │   │   ├── auth.py         # Sign-in / registration routes
│   │   │   ├── cart.py         # Shopping cart endpoints
│   │   │   ├── doctors.py      # Doctor directory & schedule endpoints
│   │   │   ├── medical_store.py# Store catalog endpoints
│   │   │   ├── patients.py     # Patient records & profile management
│   │   │   ├── payment.py      # Transaction & checkout handlers
│   │   │   └── subscription.py # Recurring prescription management
│   │   ├── core/               # App configuration and security utilities
│   │   ├── models/             # Declarative database entities (models.py)
│   │   ├── database.py         # Engine connections & session factory
│   │   └── main.py             # FastAPI entrypoint
│   └── requirements.txt        # Backend dependencies
│
└── README.md
Getting Started
Prerequisites
Node.js (v18+) & npm

Python (v3.10+)

Running instance of SQL Database (e.g., SQL Server or PostgreSQL)

Backend Setup
Clone the repository:

Bash
git clone https://github.com/Nikhil10411/centralized-medical-system.git
cd centralized-medical-system/server
Create and activate a virtual environment:

Bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

Bash
pip install -r requirements.txt
Set environment variables:
Create a .env file in the server directory:

Code snippet
DATABASE_URL=mssql+pyodbc://username:password@localhost/MedicalDB?driver=ODBC+Driver+17+for+SQL+Server
SECRET_KEY=your_super_secret_jwt_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
Start the API server:

Bash
uvicorn app.main:app --reload --port 8000
Interactive Swagger documentation will be available at http://localhost:8000/docs.

Frontend Setup
Navigate to the client folder:

Bash
cd ../client
Install node dependencies:

Bash
npm install
Configure API base URL:
Create a .env file in the client directory:

Code snippet
VITE_API_BASE_URL=http://localhost:8000
Launch the development server:

Bash
npm run dev
The application will be accessible at http://localhost:5173.

API Documentation Snapshot
Once the backend is running, visit /docs for interactive schema execution. Core exposed endpoints include:

POST /auth/login — Authenticate and retrieve bearer tokens.

GET /patients/{id}/history — Retrieve indexed patient medical history.

POST /prescriptions/assign — Upload and associate prescription records to patients.

GET /store/products — Retrieve available medical supplies and medications.

POST /cart/checkout — Initiate transaction processing via the payment handler.

Contributing
Fork the Project

Create your Feature Branch (git checkout -b feature/NewFeature)

Commit your Changes (git commit -m 'Add NewFeature')

Push to the Branch (git push origin feature/NewFeature)

Open a Pull Request


