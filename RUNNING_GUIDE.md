# Setup and Running Guide

This guide provides the exact command order to set up and run the project from scratch.

## 1. Prerequisites

- **Python 3.10+**
- **Node.js & npm** (v18+ recommended)
- **PostgreSQL** (Running locally or accessible via URL)

## 2. Backend Setup (FastAPI)

From the project root:

1.  **Create a Virtual Environment:**

    ```bash
    python -m venv venv
    ```

2.  **Activate the Virtual Environment:**
    - **Windows:**
      ```powershell
      .\venv\Scripts\activate
      ```
    - **Linux/macOS:**
      ```bash
      source venv/bin/activate
      ```

3.  **Install Dependencies:**

    ```bash
    pip install .
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory (based on `app/database.py` defaults):

    ```env
    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/filter_test_db
    ```

    _Ensure the database `filter_test_db` exists in your PostgreSQL instance._

5.  **Run Database Migrations:**

    ```bash
    alembic upgrade head
    ```

6.  **Seed Initial Data:**

    ```bash
    python seed_data.py
    ```

7.  **Start the Backend Server:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be available on the port you start Uvicorn with (default: 8000).

## 3. Frontend Setup (Angular)

Open a new terminal and navigate to the `frontend` directory:

1.  **Navigate to Frontend Folder:**

    ```bash
    cd frontend
    ```

2.  **Install Dependencies:**

    ```bash
    npm install
    ```

3.  **Start the Development Server:**
    ```bash
    npm start
    ```
    The application will be available at [http://localhost:4200](http://localhost:4200).
    During development, API requests are proxied by `frontend/proxy.conf.cjs` to the first compatible local backend (not hard-locked to port 8000).

## Summary of URLs

- **Frontend:** [http://localhost:4200](http://localhost:4200)
- **Backend API:** URL depends on your chosen backend port (e.g. [http://localhost:8000](http://localhost:8000))
- **API Documentation (Swagger):** URL depends on your chosen backend port (e.g. [http://localhost:8000/docs](http://localhost:8000/docs))
