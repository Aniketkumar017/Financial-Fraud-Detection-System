# Financial Fraud Detection System

A web-based system that helps detect and analyze potentially fraudulent financial transactions.

The system takes transaction details as input, analyzes the transaction using machine learning, calculates the fraud probability, and assigns a risk level such as **Low, Medium, High, or Critical**.

---

## Features

* User Login and Signup
* Admin Panel
* Transaction Analysis
* Fraud Probability Prediction
* Risk Level Detection
* Low, Medium, High and Critical Risk Categories
* Transaction History
* Suspicious Transaction Detection
* Fraud Alerts
* Transaction Review
* Reports and Dashboard
* User Profile
* Admin can delete transactions
* SQLite database for storing transaction and user data

---

## Technologies Used

### Frontend

* HTML
* CSS
* JavaScript

### Backend

* Python
* Flask

### Database

* SQLite

### Machine Learning

* Scikit-learn
* Logistic Regression
* Random Forest

### Other Libraries

* NumPy
* Pandas
* Joblib

---

## How the System Works

The basic working of the system is:

1. User logs into the system.
2. User enters the transaction details.
3. The system processes the given information.
4. The machine learning model analyzes the transaction.
5. A fraud probability is generated.
6. The transaction is assigned a risk level.
7. The result is stored in the database.
8. Suspicious transactions can be reviewed from the dashboard.
9. Alerts and reports help the admin monitor fraudulent activity.

---

## Risk Levels

| Risk Level | Meaning                                  |
| ---------- | ---------------------------------------- |
| Low        | Transaction has a low fraud risk         |
| Medium     | Transaction needs some attention         |
| High       | Transaction has a higher fraud risk      |
| Critical   | Transaction requires immediate attention |

---

## Project Structure

```text
Financial-Fraud-Detection-System/
│
├── app.py
├── database.py
├── requirements.txt
├── README.md
│
├── database/
│   └── fraud_detection.db
│
├── models/
│   ├── logistic_regression.pkl
│   ├── random_forest.pkl
│   ├── preprocessor.pkl
│   ├── final_features.pkl
│   ├── lr_threshold.pkl
│   └── rf_threshold.pkl
│
└── templates/
    ├── login.html
    ├── dashboard.html
    ├── prediction.html
    ├── transactions.html
    ├── transaction.html
    ├── alerts.html
    └── reports.html
```

---

## Requirements

Make sure Python is installed on your computer.

Install the required Python libraries using:

```bash
pip install -r requirements.txt
```

---

## How to Run the Project

### Step 1: Open the project folder

Open PowerShell or Command Prompt and go to the project folder:

```bash
cd Financial-Fraud-Detection-System
```

### Step 2: Install the requirements

```bash
pip install -r requirements.txt
```

### Step 3: Run the Flask application

```bash
python app.py
```

### Step 4: Open the website

After running the application, open this address in your browser:

```text
http://127.0.0.1:5000
```

---

## Login

The system contains user authentication.

Users can:

* Create an account
* Login using username or email
* Reset their password
* Access the dashboard after login

The admin account can be used to manage and review transactions.

---

## Dashboard

The dashboard provides an overview of the fraud detection system.

It shows:

* Total Transactions
* Fraud Cases
* Fraud Rate
* Critical Alerts
* Fraud Trend
* Risk Distribution
* Recent Suspicious Transactions

---

## Transaction Analysis

The **Analyze Transaction** page allows the user to enter transaction information.

After submitting the information, the system provides:

* Fraud Probability
* Risk Level
* Risk Reasons
* Recommended Action

---

## Transaction Management

The Transactions page contains the transaction history.

The admin can:

* View transaction details
* Review transactions
* Update review status
* Add review comments
* Delete transactions

---

## Alerts

The Alerts section shows suspicious transactions that require attention.

It helps the admin monitor important fraud-related activities.

---

## Reports

The Reports section provides information about:

* Fraud statistics
* Risk distribution
* Fraud trends
* Transaction analysis

---

## Machine Learning Models

The project uses machine learning models to analyze financial transactions.

The main models used are:

* Logistic Regression
* Random Forest

The trained models and supporting files are stored inside the `models` folder.

---

## Database

The project uses **SQLite** to store application data.

The database stores information such as:

* Users
* Transactions
* Fraud alerts
* Transaction reviews
* Model logs

The database file is located inside:

```text
database/fraud_detection.db
```

---

## Purpose of the Project

The main purpose of this project is to demonstrate how machine learning can be used with a web application to identify potentially fraudulent financial transactions.

It combines:

**Machine Learning + Flask + Database + Web Interface**

to create a complete fraud detection system.

---

## Author

**Aniket Kumar**

B.Tech - Computer Science Engineering
Babu Banarasi Das University, Lucknow

---

## Note

This project is developed for educational and demonstration purposes.
