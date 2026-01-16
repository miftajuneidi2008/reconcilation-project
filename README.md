
# Account Reconciliation System

A comprehensive full-stack application for managing and reconciling accounts, featuring a modern **Next.js** frontend, a **FastAPI** backend, and a **Spring Boot** demo service.

## 📂 Project Structure
After cloning, you will find the following core directories:
*   `front-end/`: The user interface built with **Next.js**.
*   `back-end/`: The core API service built with **FastAPI**.
*   `demo/`: A secondary service built with **Spring Boot**.

---

## 🚀 Getting Started

### 1. Clone the Repository
Open your terminal and run the following command to download the project:
```bash
git clone <your-repository-url>
cd <repository-folder-name>
```

---

### 2. Setting Up the Backend (FastAPI)
Navigate to the `back-end` folder to set up the Python environment and start the server.

1. **Navigate to the folder:**
   ```bash
   cd back-end
   ```
2. **Create a virtual environment:**
   *   **Windows:** `python -m venv venv`
   *   **macOS/Linux:** `python3 -m venv venv`
3. **Activate the environment:**
   *   **Windows (CMD):** `venv\Scripts\activate`
   *   **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
   *   **macOS/Linux:** `source venv/bin/activate`
4. **Install dependencies:**
   ```bash
   python -m pip install -r requirements.txt
   ```
5. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

---

### 3. Setting Up the Frontend (Next.js)
Open a **new terminal window** and navigate to the `front-end` folder.

1. **Navigate to the folder:**
   ```bash
   cd front-end
   ```
2. **Install packages:**
   Using `pnpm`:
   ```bash
   pnpm install
   ```
   *OR using `npm`:*
   ```bash
   npm install
   ```
3. **Start the development server:**
   Using `pnpm`:
   ```bash
   pnpm dev
   ```
   *OR using `npm`:*
   ```bash
   npm run dev
   ```

---

### 4. Running the Demo Service (Spring Boot)
Navigate to the demo directory. Ensure you are in the folder containing the `mvnw` file.

1. **Navigate to the directory:**
   ```bash
   cd demo
   ```
2. **Run the application:**
   *   **Using Command Prompt (Windows):**
       ```cmd
       mvnw.cmd spring-boot:run
       ```
   *   **Using Terminal (macOS/Linux/Git Bash):**
       ```bash
       ./mvnw spring-boot:run
       ```

---

## 🛠 Tech Stack
*   **Frontend:** Next.js (React), Tailwind CSS, pnpm/npm
*   **Backend:** FastAPI (Python), Uvicorn
*   **Service/Demo:** Spring Boot (Java), Maven

## 📝 Notes
*   Ensure you have **Python 3.8+**, **Node.js**, and **JDK 17+** installed on your system.
*   The FastAPI server typically runs on `http://127.0.0.1:8000`.
*   The Next.js UI typically runs on `http://localhost:3000`.