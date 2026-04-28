# Masroofy

Masroofy is a personal finance and expense tracking web application built with Django. It allows users to manage their budget, track transactions, and visualize their spending habits.

## Features

*   **User Authentication:** Secure sign-up and login functionality for users.
*   **Dashboard:** A central hub to get a quick overview of your financial status.
*   **Expense Tracking:** Easily add and categorize new expenses.
*   **Transaction History:** View a detailed history of all your past transactions.
*   **Financial Reports:** Generate reports with visual charts (using Chart.js) to understand your spending patterns.
*   **Budget Management:** Set up and manage budget cycles to keep your spending in check.
*   **User Settings:** A dedicated page for managing account settings.

## Technology Stack

*   **Backend:** Python, Django
*   **Database:** SQLite
*   **Frontend:** HTML, CSS, JavaScript

## Project Structure

The project is organized following Django best practices with a layered architecture:

```
└── masroofy/
    ├── core/            # Main application
    │   ├── dao/         # Data Access Objects for database interaction
    │   ├── models/      # Django ORM models (User, Transaction, BudgetCycle)
    │   ├── services/    # Business logic layer
    │   ├── static/      # CSS and JavaScript files
    │   ├── templates/   # HTML templates
    │   └── views/       # Handles HTTP requests and responses
    ├── masroofy/        # Django project configuration and settings
    ├── database/        # Contains the SQLite database file
    ├── manage.py        # Django's command-line utility
    └── requirements.txt # Project dependencies
```

## Getting Started

To run Masroofy on your local machine, follow these steps:

### Prerequisites

*   Python 3.x
*   pip

### Installation & Setup

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/yasminsherif200/masroofy.git
    cd masroofy
    ```

2.  **Create and activate a virtual environment (optional but recommended):**
    ```sh
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install the required dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Apply database migrations:**
    The project is configured to use SQLite, and migrations will set up the necessary tables.
    ```sh
    python manage.py migrate
    ```

5.  **Run the development server:**
    ```sh
    python manage.py runserver
    ```

The application will be available at `http://127.0.0.1:8000/`. You can create a new account to start using the app.
