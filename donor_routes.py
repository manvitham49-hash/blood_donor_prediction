from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import pandas as pd
import uuid
from datetime import datetime
from secure_email import send_otp, validate_otp
from db_helper import save_to_db_from_df
import csv


import json
import os

UPDATED_JSON = "admin_updates.json"

def get_persisted_updates():
    if os.path.exists(UPDATED_JSON):
        try:
            with open(UPDATED_JSON, 'r') as f:
                data = json.load(f)

                # Fix old data
                for k, v in data.items():
                    if isinstance(v, str):
                        data[k] = {
                            "time": v,
                            "fields": []
                        }

                return data
        except:
            return {}
    return {}

def save_persisted_updates(data):
    with open(UPDATED_JSON, "w") as f:
        json.dump(data, f)


import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          # your mysql username
        password="root123",  # put your mysql password
        database="blood_donor_db"
    )

donor_app = Blueprint("donor_app", __name__)
CSV_FILE = "blood_donor_preprocessed_dataset.csv"




# --------------------------------------------------
# Utility: Load Data
# --------------------------------------------------

def load_data():
    return pd.read_csv(CSV_FILE)


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@donor_app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        donor_id = uuid.uuid4().hex[:10]

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        # -------- CONTACT --------
        country_code = request.form.get("country_code")
        if country_code == "Others":
            country_code = request.form.get("country_code_other")

        number = request.form.get("contact_number")
        contact_number = f"{country_code} {number}"

        # -------- BASIC --------
        blood_group = request.form["blood_group"]
        availability = request.form["availability"]

        months_since_first_donation = int(request.form["months"])
        number_of_donation = int(request.form["donations"])
        pints_donated = float(request.form["pints"])

        # -------- MEDICAL --------
        haemoglobin = request.form["haemoglobin"]
        platelets = request.form["platelets"]
        blood_pressure = request.form["blood_pressure"]
        gender = request.form["gender"]

        last_donation_raw = request.form["last_blood_donation_date"]

        if last_donation_raw:
            last_blood_donation_date = datetime.strptime(
                last_donation_raw, "%Y-%m-%d"
            ).strftime("%m/%d/%Y")

            days_since_last_donation = (
                datetime.now() - datetime.strptime(last_blood_donation_date, "%m/%d/%Y")
            ).days
        else:
            last_blood_donation_date = ""
            days_since_last_donation = 0

        # -------- DOB --------
        dob_raw = request.form["date_of_birth"]
        date_of_birth = datetime.strptime(
            dob_raw, "%Y-%m-%d"
        ).strftime("%m/%d/%Y")

        current_age = request.form["current_age"]
        age_at_time_of_registration = request.form["age_at_time_of_registration"]

        current_age = int(current_age)
        
        if current_age < 18 or current_age > 65:
            flash("❌ Age must be between 18 and 65 to register as a donor")
            return redirect(url_for("donor_app.register"))

        created_at = datetime.now().strftime("%m/%d/%Y")

        # -------- HELPER FUNCTION --------
        def get_value(field):
            val = request.form.get(field)
            if val == "Others":
                return request.form.get(field + "_other")
            return val

        # -------- PERMANENT --------
        permanent_state = get_value("permanent_state")
        permanent_district = get_value("permanent_district")
        permanent_city = get_value("permanent_city")
        permanent_street = get_value("permanent_street")
        permanent_pincode = request.form.get("permanent_pincode")

        # -------- CURRENT --------
        current_state = get_value("current_state")
        current_district = get_value("current_district")
        current_city = get_value("current_city")
        current_street = get_value("current_street")
        current_pincode = request.form.get("current_pincode")

        # -------- SAVE TO CSV --------
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                donor_id, name, email, password, contact_number,
                blood_group, availability,
                months_since_first_donation,
                number_of_donation, pints_donated,

                created_at, date_of_birth,
                current_age, age_at_time_of_registration,

                permanent_city, permanent_state,
                permanent_district, permanent_pincode,
                permanent_street,

                current_city, current_state,
                current_district, current_pincode,
                current_street,

                "No",

                haemoglobin,
                platelets,
                gender,
                last_blood_donation_date,
                days_since_last_donation,
                blood_pressure
            ])

        # -------- SAVE TO MYSQL --------
        created_at_db = datetime.strptime(created_at, "%m/%d/%Y")
        date_of_birth_db = datetime.strptime(date_of_birth, "%m/%d/%Y")

        if last_blood_donation_date:
            last_donation_db = datetime.strptime(last_blood_donation_date, "%m/%d/%Y")
        else:
            last_donation_db = None

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO donors (

            donor_id, name, email, password, contact_number,
            blood_group, availability,
            months_since_first_donation,
            number_of_donation, pints_donated,
            created_at, date_of_birth,
            current_age, age_at_time_of_registration,
            permanent_city, permanent_state,
            permanent_district, permanent_pincode,
            permanent_street,
            current_city, current_state,
            current_district, current_pincode,
            current_street,
            donor_details_updated_by_admin,
            status,
            haemoglobin,
            platelets,
            gender,
            last_blood_donation_date,
            days_since_last_donation,
            blood_pressure
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (

            donor_id, name, email, password, contact_number,
            blood_group, availability,
            months_since_first_donation,
            number_of_donation, pints_donated,

            created_at_db, date_of_birth_db,
            current_age, age_at_time_of_registration,

            permanent_city, permanent_state,
            permanent_district, permanent_pincode,
            permanent_street,

            current_city, current_state,
            current_district, current_pincode,
            current_street,

            "No",
            "Active",  

            haemoglobin,
            platelets,
            gender,
            last_donation_db,
            days_since_last_donation,
            blood_pressure
        ))

        conn.commit()
        conn.close()

        print("✅ NEW DONOR INSERTED")

        flash("Registration successful!")
        return redirect(url_for("donor_app.register"))

    return render_template("register.html")

# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@donor_app.route("/login", methods=["GET","POST"])
def login():

    df = load_data()
    df["email"] = df["email"].astype(str).str.strip()
    df["password"] = df["password"].astype(str).str.strip()

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"].strip()

        donor = df[
            (df["email"] == email) &
            (df["password"] == password)
        ]

        if donor.empty:
            return render_template(
                "login.html",
                error="Invalid email or password"
            )

        donor = donor.iloc[0]
        session["donor_id"] = donor["donor_id"]
        session["role"] = "donor"

        return redirect(url_for("donor_app.donor_profile"))

    return render_template("login.html")


# --------------------------------------------------
# PROFILE
# --------------------------------------------------

@donor_app.route("/profile")
def profile():

    if "donor_id" not in session:
        return redirect(url_for("donor_app.login"))

    donor_id = str(session["donor_id"]).strip()

    # VERY IMPORTANT → read as string
    df = pd.read_csv(CSV_FILE, dtype=str)

    df["donor_id"] = df["donor_id"].astype(str).str.strip()

    donor_row = df[df["donor_id"] == donor_id]

    if donor_row.empty:
        return "Donor not found", 404

    donor = donor_row.iloc[0].to_dict()

    # Clean NaN values safely
    for key in donor:
        if pd.isna(donor[key]) or donor[key] == "nan":
            donor[key] = ""

    # -------- CONTACT FIX --------
    donor["contact"] = donor.get("contact_number", "").strip() or "N/A"

    # -------- FORMAT CITY --------
    donor["permanent_city"] = donor.get("permanent_city") or "N/A"
    donor["current_city"] = donor.get("current_city") or "N/A"

    # -------- FORMAT BLOOD DETAILS --------
    donor["months_since_first_donation"] = donor.get("months_since_first_donation") or ""
    donor["number_of_donation"] = donor.get("number_of_donation") or ""
    donor["pints_donated"] = donor.get("pints_donated") or ""

    # -------- FORMAT MEDICAL DETAILS --------
    donor["haemoglobin"] = donor.get("haemoglobin") or "N/A"
    donor["platelets"] = donor.get("platelets") or "N/A"
    donor["blood_pressure"] = donor.get("blood_pressure") or "N/A"
    donor["gender"] = donor.get("gender") or "N/A"
    donor["last_blood_donation_date"] = donor.get("last_blood_donation_date") or "N/A"
    donor["days_since_last_donation"] = donor.get("days_since_last_donation") or "N/A"

    updates = get_persisted_updates()
    donor_data = updates.get(donor_id, {})
    status = donor_data.get("status")
    if not status:
         status = "active"
    print("DEBUG STATUS:", updates.get(str(donor_id)))


    return render_template("profile.html", donor=donor, updated_map=updates, status=status)

# --------------------------------------------------
# UPDATE PROFILE
# --------------------------------------------------

@donor_app.route("/update-profile", methods=["GET", "POST"])
def update_profile():

    if session.get("role") != "donor":
        return redirect(url_for("donor_app.login"))

    donor_id = str(session["donor_id"]).strip()
    df = load_data()

    # 🔥 IMPORTANT → ensure matching works
    df["donor_id"] = df["donor_id"].astype(str).str.strip()

    donor_row = df[df["donor_id"] == donor_id]
    if donor_row.empty:
        return "Donor not found", 404

    idx = donor_row.index[0]
    donor = donor_row.iloc[0].to_dict()

    for key in donor:
        if pd.isna(donor[key]):
            donor[key] = ""

    from datetime import datetime

    dob_for_input = ""
    if donor.get("date_of_birth"):
        try:
            dob_for_input = datetime.strptime(
                donor["date_of_birth"], "%m/%d/%Y"
            ).strftime("%Y-%m-%d")
        except:
            pass

    last_donation_for_input = ""
    if donor.get("last_blood_donation_date"):
        try:
            last_donation_for_input = datetime.strptime(
                donor["last_blood_donation_date"], "%m/%d/%Y"
            ).strftime("%Y-%m-%d")
        except:
            pass
    
    success = False 

    if request.method == "POST":

        def get_value(field):
            val = request.form.get(field)
            if val == "Others":
                return request.form.get(field + "_other")
            return val

        # -------- UPDATE CSV --------
        df.at[idx, "name"] = request.form["name"].strip()
        df.at[idx, "email"] = request.form["email"].strip()

        country_code = request.form.get("country_code")
        if country_code == "Others":
            country_code = request.form.get("country_code_other")

        number = request.form.get("contact_number")
        df.at[idx, "contact_number"] = f"{country_code} {number}"

        # Address
        df.at[idx, "permanent_city"] = get_value("permanent_city")
        df.at[idx, "permanent_state"] = get_value("permanent_state")
        df.at[idx, "permanent_district"] = get_value("permanent_district")
        df.at[idx, "permanent_street"] = get_value("permanent_street")
        df.at[idx, "permanent_pincode"] = request.form.get("permanent_pincode")

        df.at[idx, "current_city"] = get_value("current_city")
        df.at[idx, "current_state"] = get_value("current_state")
        df.at[idx, "current_district"] = get_value("current_district")
        df.at[idx, "current_street"] = get_value("current_street")
        df.at[idx, "current_pincode"] = request.form.get("current_pincode")

        # Blood
        df.at[idx, "blood_group"] = request.form["blood_group"]
        df.at[idx, "availability"] = request.form["availability"]
        df.at[idx, "months_since_first_donation"] = request.form["months"]
        df.at[idx, "number_of_donation"] = request.form["donations"]
        df.at[idx, "pints_donated"] = request.form["pints"]
        df.at[idx, "haemoglobin"] = request.form["haemoglobin"]
        df.at[idx, "platelets"] = request.form["platelets"]
        df.at[idx, "blood_pressure"] = request.form["blood_pressure"]
        df.at[idx, "gender"] = request.form["gender"]

        # Dates
        if request.form.get("last_blood_donation_date"):
            db_last = request.form.get("last_blood_donation_date")
            formatted = datetime.strptime(db_last, "%Y-%m-%d").strftime("%m/%d/%Y")
            df.at[idx, "last_blood_donation_date"] = formatted
            df.at[idx, "days_since_last_donation"] = (
                datetime.today() - datetime.strptime(db_last, "%Y-%m-%d")
            ).days

        # -------- DOB FIX --------
        if request.form.get("date_of_birth"):
            dob = request.form.get("date_of_birth")  
            dob_obj = datetime.strptime(dob, "%Y-%m-%d")
            today = datetime.today()
            age = today.year - dob_obj.year - (
                (today.month, today.day) < (dob_obj.month, dob_obj.day)
            )
            if age < 18 or age > 65:
                flash("❌ Age must be between 18 and 65")
                return redirect(url_for("donor_app.update_profile"))
            formatted_dob = dob_obj.strftime("%m/%d/%Y")
            df.at[idx, "date_of_birth"] = formatted_dob
            df.at[idx, "current_age"] = age
            df.at[idx, "age_at_time_of_registration"] = age

           
        # -------- SAVE CSV --------
        df.to_csv(CSV_FILE, index=False)

        # -------- 🔥 FINAL FIX: SYNC FULL ROW --------
        updated_row = df.loc[idx]

        # ensure no NaN
        updated_row = updated_row.fillna("")

        # convert to tuple in correct order
        db_data = tuple(updated_row.tolist())

        print(">>> Syncing donor:", donor_id)

        from db_helper import save_to_db_from_df
        save_to_db_from_df(updated_row)

        success = True
        print(">>> SUCCESS FLAG SET")
        

    return render_template(
        "update_profile.html",
        donor=donor,
        success=success,
        dob_for_input=dob_for_input,
        last_donation_for_input=last_donation_for_input
    )

# --------------------------------------------------
# SEND MESSAGE
# --------------------------------------------------

@donor_app.route("/profile-message")
def donor_profile():

    if "donor_id" not in session:
        return redirect(url_for("donor_app.login"))

    donor_id = session.get("donor_id")

    df = load_data()

    donor = df[df["donor_id"] == donor_id].iloc[0]

    # 🔥 FIX: Strict condition (only True allowed)
    if donor.get("donor_details_updated_by_admin") == True:
        flash("Admin has updated your details. Please verify.")

    updates = get_persisted_updates()
    donor_id = str(donor_id)

    status = updates.get(donor_id, {}).get("status", "active")

    return render_template(
        "profile.html",
        donor=donor,
        updated_map=updates,
        status=status

    )

# --------------------------------------------------
# VERIFY ADDRESS
# --------------------------------------------------

@donor_app.route("/verify-admin-update")
def verify_admin_update():

    donor_id = str(session.get("donor_id"))

    # -------- REMOVE FROM JSON --------
    updates = get_persisted_updates()

    if donor_id in updates:
        updates.pop(donor_id)

    save_persisted_updates(updates)

    # -------- UPDATE CSV FLAG --------
    df = load_data()
    df.loc[df["donor_id"] == donor_id, "donor_details_updated_by_admin"] = "No"
    df.to_csv(CSV_FILE, index=False)


    # -------- 🔥 UPDATE MYSQL ALSO --------
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE donors
        SET donor_details_updated_by_admin = 'No'
        WHERE donor_id = %s
    """, (donor_id,))

    conn.commit()
    conn.close()

    print("✅ VERIFIED → DB + CSV UPDATED")

    return redirect(url_for("donor_app.profile"))

# --------------------------------------------------
# FORGOT PASSWORD
# --------------------------------------------------


@donor_app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]

        df = load_data()

        if email not in df["email"].values:
            return render_template("forgot.html", error="Email not found")

        send_otp(email)
        return redirect(url_for("donor_app.verify_otp", email=email))

    return render_template("forgot.html")


# --------------------------------------------------
# VERIFY OTP
# --------------------------------------------------
@donor_app.route("/verify-otp/<email>", methods=["GET", "POST"])
def verify_otp(email):
    if request.method == "POST":
        user_otp = request.form["otp"]
        result = validate_otp(email, user_otp)

        if result == "OK":
            return redirect(url_for("donor_app.reset_password", email=email))
        else:
            return render_template("otp_verify.html", error=result)

    return render_template("otp_verify.html")


# --------------------------------------------------
# RESET PASSWORD
# --------------------------------------------------
@donor_app.route("/reset-password/<email>", methods=["GET", "POST"])
def reset_password(email):
    if request.method == "POST":
        new_pass = request.form["password"]

        df = load_data()
        df.loc[df["email"] == email, "password"] = new_pass
        df.to_csv(CSV_FILE, index=False)

        flash("Password updated!", "success")
        return redirect(url_for("donor_app.login"))

    return render_template("reset_password.html")





# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@donor_app.route("/logout")
def donor_logout():
    session.clear()
    return redirect(url_for("donor_app.login"))