# Blood Donor Prediction System

A Flask-based web application that predicts blood donor eligibility using a machine learning model and provides a complete donor management system. The application allows users to register, log in, manage donor profiles, track donation history, and enables administrators to manage donor records through a secure dashboard.

## Project Overview

The Blood Donor Prediction System is designed to assist blood donation organizations and healthcare institutions in identifying potential blood donors based on health-related parameters. The system integrates machine learning with a user-friendly web interface to improve donor management and eligibility prediction.

## Features

* Donor registration and secure login
* Blood donor eligibility prediction
* Admin login and dashboard
* View and manage donor records
* Update donor profiles
* Donation history management
* Password reset and OTP verification
* Secure user authentication
* Machine learning-based prediction model
* Responsive web interface

## Tech Stack

### Frontend

* HTML5
* CSS3
* Bootstrap

### Backend

* Python
* Flask

### Database

* SQLite

### Machine Learning

* Scikit-learn
* Pandas
* NumPy

## Project Structure

blood_donor_prediction/
│
├── templates/
├── static/
├── app.py
├── train_model.py
├── verify_ids.py
├── requirements.txt
└── README.md

## Installation

### Clone the repository

git clone https://github.com/manvitham49-hash/blood_donor_prediction.git

### Navigate to the project directory

cd blood_donor_prediction

### Install dependencies

pip install -r requirements.txt

### Run the application

python app.py

### Open in your browser

http://127.0.0.1:5000

## Machine Learning Model

The application uses a classification model trained with **Scikit-learn** to predict donor eligibility based on health-related input parameters. The trained model is integrated into the Flask application to provide real-time prediction results.

## Admin Module

The administrator dashboard includes:

* View registered donors
* Update donor information
* Verify donor details
* Monitor donation history
* Manage user accounts

## Application Workflow

1. User registers with personal and health details.
2. User logs into the system.
3. Health information is submitted.
4. The machine learning model predicts donor eligibility.
5. The result is displayed to the user.
6. The administrator can view and manage donor records.

## Currently Learning

I am currently pursuing **Master of Computer Applications (MCA) (2026–2028)** at **SRM Institute of Science and Technology (SRMIST), Kattankulathur (KTR) Campus, Chennai**.

I am actively learning and building projects in:

* Data Structures and Algorithms (DSA)
* Java Programming
* Python for Backend Development
* Flask and Web Application Development
* SQL and Database Management
* Machine Learning
* Git and GitHub
* Software Engineering Principles

## Future Enhancements

* Blood inventory management
* Hospital integration
* Email and SMS notifications
* Advanced donor matching
* Real-time analytics dashboard
* Cloud database integration
* Appointment scheduling
* Mobile application support

## Academic Project

This project was developed as part of the **Bachelor of Computer Applications (BCA)** program at **GITAM University, Visakhapatnam** during **2023–2026**.

## Author

**D. V. Sree Manvitha**

BCA (2023–2026), GITAM University, Visakhapatnam

Currently pursuing MCA (2026–2028) at **SRM Institute of Science and Technology (SRMIST), Kattankulathur (KTR) Campus, Chennai**

GitHub: https://github.com/manvitham49-hash

## License

This project is developed for educational and academic purposes.


## Live Demo

https://blood-donor-prediction-1.onrender.com
