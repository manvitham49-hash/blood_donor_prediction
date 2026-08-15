from flask import Blueprint, render_template, request, session, redirect, flash, url_for
import pandas as pd
import pickle
import json
import os
from datetime import datetime
from secure_email import send_otp, validate_otp

# --- NEW: JSON Persistence Helpers ---
UPDATED_JSON = "admin_updates.json"

def get_persisted_updates():
    if os.path.exists(UPDATED_JSON):
        try:
            with open(UPDATED_JSON, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_persisted_updates(data):
    with open(UPDATED_JSON, 'w') as f:
        json.dump(data, f)

# --------------------------------------------------
# Blueprint
# --------------------------------------------------

admin_app = Blueprint("admin_app", __name__)

CSV_FILE = "blood_donor_preprocessed_dataset.csv"

ADMIN_EMAIL = "dvsprasad88@gmail.com"
ADMIN_PASSWORD = "admin123"


# --------------------------------------------------
# Load ML Model
# --------------------------------------------------

model, preprocessor = pickle.load(open("model.pkl", "rb"))


# --------------------------------------------------
# Load CSV
# --------------------------------------------------

def load_data():

    df = pd.read_csv(CSV_FILE)

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    if "status" not in df.columns:
        df["status"] = "active"

    df["status"] = df["status"].fillna("active")

    return df


# --------------------------------------------------
# ADMIN LOGIN
# --------------------------------------------------

@admin_app.route("/admin-login", methods=["GET","POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email")
        pwd = request.form.get("password")

        if email == ADMIN_EMAIL and pwd == ADMIN_PASSWORD:

            session["role"] = "admin"
            return redirect("/admin-options")

        return render_template("admin_login.html", error="Invalid Credentials")

    return render_template("admin_login.html")


# --------------------------------------------------
# ADMIN OPTIONS
# --------------------------------------------------

@admin_app.route("/admin-options")
def admin_options():

    if session.get("role") != "admin":
        return redirect("/admin-login")

    return render_template("admin_options.html")


# --------------------------------------------------
# ADMIN PREDICTION
# --------------------------------------------------

# --------------------------------------------------
# ADMIN PREDICTION
# --------------------------------------------------

@admin_app.route("/admin-predict", methods=["GET","POST"])
def admin_predict():
    
    all_probs = {}
    selected_city = None
    selected_group = None
    group_prob = None

    if session.get("role") != "admin":
        return redirect("/admin-login")

    df = load_data()
    updates = get_persisted_updates()

    # REMOVE BLOCKED DONORS
    df = df[~df["donor_id"].astype(str).isin(
        [k for k, v in updates.items() if v.get("status") == "blocked"]
    )]

    df["current_city"] = df["current_city"].astype(str).str.strip()
    df["blood_group"] = df["blood_group"].astype(str).str.strip()

    df["haemoglobin"] = pd.to_numeric(df["haemoglobin"], errors="coerce")
    df["platelets"] = pd.to_numeric(df["platelets"], errors="coerce")
    df["days_since_last_donation"] = pd.to_numeric(df["days_since_last_donation"], errors="coerce")

    cities = sorted(df["current_city"].dropna().unique())
    blood_groups = sorted(df["blood_group"].dropna().unique())

    probability = None
    prediction_label = None

    individual_predictions = []
    high_probability = []
    moderate_probability = []
    low_probability = []

    no_donors = False
    city = ""
    blood = ""

    if request.method == "POST":

        selected_city = request.form.get("city")
        selected_group = request.form.get("blood_group")

        selected_option = request.form.get("city","").strip()

        # ✅ FIX FOR "OTHERS"
        if selected_option == "Others":
            city = request.form.get("city_other","").strip()
        else:
            city = selected_option  

        selected_city = city
        blood = request.form.get("blood_group","").strip()

        # --------------------------------------------------
        # ALL BLOOD GROUP PROBABILITIES
        # --------------------------------------------------
        for bg in blood_groups:

            city_filtered = df[
                (df["current_city"].str.lower() == city.lower()) &
                (df["blood_group"].str.lower() == bg.lower())
            ]

            if city_filtered.empty:
                all_probs[bg] = 0
                continue

            features = city_filtered[[
                "current_city",
                "blood_group",
                "months_since_first_donation",
                "number_of_donation",
                "pints_donated",
                "haemoglobin",
                "platelets",
                "days_since_last_donation"
            ]].copy()

            # ADD REQUIRED COLUMNS
            features["current_age"] = 30
            features["age_at_time_of_registration"] = 25

            features = features[[
                "current_age",
                "age_at_time_of_registration",
                "months_since_first_donation",
                "number_of_donation",
                "pints_donated",
                "haemoglobin",
                "platelets",
                "days_since_last_donation",
                "current_city",
                "blood_group"
            ]]

            features_processed = preprocessor.transform(features)
            probs = model.predict_proba(features_processed)[:, 1]

            all_probs[bg] = round(float(probs.mean()), 4)

        group_prob = all_probs.get(selected_group, 0)

        # --------------------------------------------------
        # FILTER DATA
        # --------------------------------------------------
        if not city:
            no_donors = True
        else:
            filtered = df[
                (df["current_city"].str.lower() == city.lower()) &
                (df["blood_group"].str.lower() == blood.lower())
            ]

            if filtered.empty:
                no_donors = True

        # --------------------------------------------------
        # MAIN PREDICTION
        # --------------------------------------------------
        if not no_donors:

            features = filtered[[
                "current_city",
                "blood_group",
                "months_since_first_donation",
                "number_of_donation",
                "pints_donated",
                "haemoglobin",
                "platelets",
                "days_since_last_donation"
            ]].copy()

            features["current_age"] = 30
            features["age_at_time_of_registration"] = 25

            features = features[[
                "current_age",
                "age_at_time_of_registration",
                "months_since_first_donation",
                "number_of_donation",
                "pints_donated",
                "haemoglobin",
                "platelets",
                "days_since_last_donation",
                "current_city",
                "blood_group"
            ]]

            features_processed = preprocessor.transform(features)
            probabilities = model.predict_proba(features_processed)[:, 1]

            probability = round(float(probabilities.mean()), 4)

            if probability >= 0.7:
                prediction_label = "High Availability"
            elif probability >= 0.4:
                prediction_label = "Moderate Availability"
            else:
                prediction_label = "Low Availability"

            # --------------------------------------------------
            # INDIVIDUAL DONOR LOOP (FIXED)
            # --------------------------------------------------
            from datetime import datetime

            for donor, prob in zip(filtered.to_dict("records"), probabilities):

                prob = round(float(prob), 4)

                if prob >= 0.7:
                    status = "Likely Available"
                elif prob >= 0.4:
                    status = "Moderate"
                else:
                    status = "Less Likely"

                # AGE
                dob = str(donor.get("date_of_birth", "")).strip()
                try:
                    dob_date = pd.to_datetime(dob)
                    today = datetime.today()
                    age = today.year - dob_date.year - (
                        (today.month, today.day) < (dob_date.month, dob_date.day)
                    )
                except:
                    age = "N/A"

                # HEALTH
                hb = pd.to_numeric(donor.get("haemoglobin"), errors="coerce")
                platelets = pd.to_numeric(donor.get("platelets"), errors="coerce")
                bp = str(donor.get("blood_pressure", "0/0"))

                try:
                    sys_bp, dia_bp = map(int, bp.split("/"))
                except:
                    sys_bp, dia_bp = 0, 0

                gender = str(donor.get("gender", "")).lower()

                hb_normal = False
                if not pd.isna(hb):
                    if gender == "male":
                        hb_normal = 13 <= hb <= 17
                    else:
                        hb_normal = 12 <= hb <= 15

                platelet_normal = not pd.isna(platelets) and (150000 <= platelets <= 450000)
                bp_normal = 90 <= sys_bp <= 140 and 60 <= dia_bp <= 90

               
                reasons = []
                # Haemoglobin
                if pd.isna(hb):
                    reasons.append("Hb Unknown")
                else:
                    if gender == "male" and hb < 13:
                        reasons.append("Low Haemoglobin")
                    elif gender == "female" and hb < 12:
                        reasons.append("Low Haemoglobin")
                    elif hb > 17:
                        reasons.append("High Haemoglobin")

                # Platelets
                if pd.isna(platelets):
                    reasons.append("Platelets Unknown")
                else:
                    if platelets < 150000:
                        reasons.append("Low Platelets")
                    elif platelets > 450000:
                        reasons.append("High Platelets")

                # Blood Pressure
                if not (90 <= sys_bp <= 140 and 60 <= dia_bp <= 90):
                    reasons.append("Abnormal BP")

                # Donation gap
                days = donor.get("days_since_last_donation", 0)
                if pd.notna(days) and days < 90:
                    reasons.append("Recently Donated (<90 days)")

                # Final decision
                if len(reasons) == 0:
                    health_condition = "Normal"
                    eligibility = "Eligible"
                    reason_text = "Healthy"
                else:
                    health_condition = "Not Normal"
                    eligibility = "Not Eligible"
                    reason_text = ", ".join(reasons)

           

                donor_data = {
                    "name": donor.get("name"),
                    "age": age,
                    "gender": donor.get("gender"),
                    "contact": donor.get("contact_number"),
                    "status": status,
                    "probability": prob,
                    "haemoglobin": donor.get("haemoglobin"),
                    "platelets": donor.get("platelets"),
                    "blood_pressure": donor.get("blood_pressure"),
                    "last_donation_date": donor.get("last_blood_donation_date"),
                    "days_since_last_donation": donor.get("days_since_last_donation"),
                    "health_condition": health_condition,
                    "eligibility": eligibility,
                    "reason": reason_text,

                    "current_city": donor.get("current_city")
                }

                individual_predictions.append(donor_data)

                if prob >= 0.7:
                    high_probability.append(donor_data)
                elif prob >= 0.4:
                    moderate_probability.append(donor_data)
                else:
                    low_probability.append(donor_data)

    selected_option = request.form.get("city", "")

    return render_template(
        "admin_predict.html",
        cities=cities,
        blood_groups=blood_groups,
        probability=probability,
        prediction_label=prediction_label,
        individual_predictions=individual_predictions,
        high_probability=high_probability,
        moderate_probability=moderate_probability,
        low_probability=low_probability,
        selected_city=city,
        selected_blood=blood,
        selected_option=selected_option, 
        all_probs=all_probs,
        selected_group=selected_group,
        group_prob=group_prob,
        no_donors=no_donors
    )

# --------------------------------------------------
# ADMIN FULL DONOR UPDATE
# --------------------------------------------------

@admin_app.route("/admin-update-donor/<donor_id>", methods=["GET", "POST"])
def donor_details_updated_by_admin(donor_id):

    if session.get("role") != "admin":
        return redirect("/admin-login")

    donor_id = str(donor_id).strip()

    df = pd.read_csv(CSV_FILE, dtype=str)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["donor_id"] = df["donor_id"].astype(str).str.strip()

    donor_row = df[df["donor_id"] == donor_id]

    if donor_row.empty:
        return "Donor not found"

    idx = donor_row.index[0]
    donor = donor_row.iloc[0].to_dict()

    # Clean NaN
    for key in donor:
        if pd.isna(donor[key]) or donor[key] == "nan":
            donor[key] = ""

    from datetime import datetime

    # -------- FORMAT DOB --------
    dob_for_input = ""
    if donor.get("date_of_birth"):
        try:
            dob_for_input = datetime.strptime(
                donor["date_of_birth"], "%m/%d/%Y"
            ).strftime("%Y-%m-%d")
        except:
            pass

    # -------- FORMAT LAST DONATION --------
    last_donation_for_input = ""
    if donor.get("last_blood_donation_date"):
        try:
            last_donation_for_input = datetime.strptime(
                donor["last_blood_donation_date"], "%m/%d/%Y"
            ).strftime("%Y-%m-%d")
        except:
            pass

    success_msg = None
    redirect_after_update = False

    if request.method == "POST":


        updated_fields = []

        def track(field, new_value):
            old_value = str(df.at[idx, field]).strip()
            if str(new_value).strip() != old_value:
                updated_fields.append(field)
            df.at[idx, field] = new_value

        def get_value(field):
            val = request.form.get(field)
            if val == "Others":
                return request.form.get(field + "_other")
            return val

        # -------- UPDATE CSV --------
        

        track("name", request.form["name"])

        country_code = request.form.get("country_code")
        if country_code == "Others":
            country_code = request.form.get("country_code_other")

        number = request.form.get("contact_number")
        track("contact_number", f"{country_code} {number}")

        track("blood_group", request.form["blood_group"])
        track("availability", request.form["availability"])
        track("gender", request.form["gender"])

        # DOB + Age
      
        if request.form.get("date_of_birth"):
             dob = request.form.get("date_of_birth")
             dob_obj = datetime.strptime(dob, "%Y-%m-%d")
             today = datetime.today()

             age = today.year - dob_obj.year - (
                 (today.month, today.day) < (dob_obj.month, dob_obj.day)
             )

             
             if age < 18 or age > 65:
                 flash("❌ Age must be between 18 and 65", "error")
                 return redirect(url_for("admin_app.donor_details_updated_by_admin", donor_id=donor_id))

             # ✅ FORMAT + SAVE
             formatted_dob = dob_obj.strftime("%m/%d/%Y")

             track("date_of_birth", formatted_dob)
             track("current_age", age)


        # Donation
        track("months_since_first_donation", request.form["months"])
        track("number_of_donation", request.form["donations"])
        track("pints_donated", request.form["pints"])

        # Last donation
        if request.form.get("last_blood_donation_date"):
            db_last = request.form.get("last_blood_donation_date")

            formatted = datetime.strptime(db_last, "%Y-%m-%d").strftime("%m/%d/%Y")

            track("last_blood_donation_date", formatted)
    
           
            today = datetime.today()
            days = (today - datetime.strptime(db_last, "%Y-%m-%d")).days
            track("days_since_last_donation", days)        


        # Medical
        track("haemoglobin", request.form["haemoglobin"])
        track("platelets", request.form["platelets"])
        track("blood_pressure", request.form["blood_pressure"])        


        # Addresses
        track("permanent_city", get_value("permanent_city"))
        track("permanent_state", get_value("permanent_state"))
        track("permanent_district", get_value("permanent_district"))
        track("permanent_pincode", request.form.get("permanent_pincode"))
        track("permanent_street", get_value("permanent_street"))

        track("current_city", get_value("current_city"))
        track("current_state", get_value("current_state"))
        track("current_district", get_value("current_district"))
        track("current_pincode", request.form.get("current_pincode"))
        track("current_street", get_value("current_street"))

        df.at[idx, "donor_details_updated_by_admin"] = "Yes"

        # -------- SAVE UPDATE TIMESTAMP --------
        updates = get_persisted_updates()
        updates.setdefault(str(donor_id), {})
        updates[str(donor_id)]["time"] = datetime.now().isoformat()
        updates[str(donor_id)]["fields"] = updated_fields
        

        save_persisted_updates(updates)

        # -------- SAVE CSV --------
        df.to_csv(CSV_FILE, index=False)

        # -------- 🔥 FINAL FIX: SYNC FULL ROW --------
        updated_row = df.loc[idx]
        updated_row = updated_row.fillna("")

        from db_helper import save_to_db_from_df

        print(">>> Admin syncing:", donor_id)
        save_to_db_from_df(updated_row)

        success_msg = "Donor details updated successfully!"
        redirect_after_update = True

    return render_template(
        "donor_details_updated_by_admin.html",
        donor=donor,
        dob_for_input=dob_for_input,
        last_donation_for_input=last_donation_for_input,
        success_msg=success_msg,
        redirect_after_update=redirect_after_update
    )

# --------------------------------------------------
# ADMIN ROUTE TO SHOW DONORS
# --------------------------------------------------


@admin_app.route("/admin-donors", methods=["GET","POST"])
def admin_donors():
    from datetime import datetime, timedelta

    updated_map = get_persisted_updates()

    
    df = load_data()
    cities = sorted(df["current_city"].dropna().unique())

    # 2. Collect Inputs
    city = None
    blood = None
    filter_type = request.values.get("filter") 

    if request.method == "POST":
        city = request.form.get("city")
        blood = request.form.get("blood_group")
        if city == "Others":
            city = request.form.get("city_other")
    else:
        city = request.args.get("city")
        blood = request.args.get("blood_group")

    # 3. Time-based Expiry Logic (Set to 7 Days)
    valid_recently_updated_ids = []
    now = datetime.now()
    
    for d_id, data in updated_map.items():
        try:
            update_time = datetime.fromisoformat(data.get("time"))
            # Logic: Show only if updated within the last 7 days
            if now - update_time <= timedelta(days=7):
                valid_recently_updated_ids.append(str(d_id))
        except:
            continue

    valid_recently_blocked_ids = []
    valid_recently_unblocked_ids = []

    for d_id, data in updated_map.items():
        try:
            # BLOCKED
            if data.get("blocked_time"):
                bt = datetime.fromisoformat(data.get("blocked_time"))
                if now - bt <= timedelta(days=7):
                    valid_recently_blocked_ids.append(str(d_id))

            # UNBLOCKED
            if data.get("unblocked_time"):
                ut = datetime.fromisoformat(data.get("unblocked_time"))
                if now - ut <= timedelta(days=7):
                    valid_recently_unblocked_ids.append(str(d_id))

        except:
            continue


    # 4. Apply Filtering (Preserving CSV check + Time check)
    filtered = df.copy()

    if filter_type == "admin_updated":
        # Must be in the 7-day session list AND have 'Yes' in the CSV column
        time_filter = filtered["donor_id"].astype(str).isin(valid_recently_updated_ids)
        csv_filter = filtered["donor_details_updated_by_admin"].astype(str).str.strip().isin(["Yes","True","1"])
        
        filtered = filtered[time_filter & csv_filter]


    elif filter_type == "blocked":
        filtered = filtered[
            filtered["donor_id"].astype(str).isin(valid_recently_blocked_ids) &
            filtered["donor_id"].astype(str).apply(
                lambda x: updated_map.get(x, {}).get("status") == "blocked"
            )
            
        ]

    elif filter_type == "unblocked":
        filtered = filtered[
            filtered["donor_id"].astype(str).isin(valid_recently_unblocked_ids) &
            filtered["donor_id"].astype(str).apply(
                lambda x: updated_map.get(x, {}).get("status") == "active"
            )   
        ]

    elif filter_type == "history":

        valid_history_ids = []

        for d_id, data in updated_map.items():
            history = data.get("history", [])

            for h in history:
                try:
                    h_time = datetime.fromisoformat(h.get("time"))

                    if now - h_time <= timedelta(days=180):
                        valid_history_ids.append(str(d_id))
                        break
                except:
                    continue

        filtered = filtered[
            filtered["donor_id"].astype(str).isin(valid_history_ids)
        ]                


    

    if city:
        filtered = filtered[filtered["current_city"] == city]

    if blood:
        filtered = filtered[filtered["blood_group"] == blood]

    # 5. Prepare Data for Template
    donors = filtered.to_dict("records")

    for d in donors:

        donor_id = str(d.get("donor_id"))
        
        data = updated_map.get(donor_id, {})

        history = data.get("history", [])
        filtered_history = []

        now = datetime.now()

        for h in history:
            try:
                h_time = datetime.fromisoformat(h.get("time"))

                if now - h_time <= timedelta(days=180):
                    filtered_history.append({
                        "action": h.get("action"),
                        "time": h_time.strftime("%d/%m/%Y %I:%M %p")
                    })
            except:
                continue

        d["history"] = filtered_history[::-1]  

        # BLOCKED
        if data.get("blocked_time"):
            try:
                bt = datetime.fromisoformat(data.get("blocked_time"))
                d["blocked_date"] = bt.strftime("%d/%m/%Y")
                d["blocked_time"] = bt.strftime("%I:%M %p")
            except:
                d["blocked_date"] = ""
                d["blocked_time"] = ""
        else:
            d["blocked_date"] = ""
            
            

        # UNBLOCKED
        if data.get("unblocked_time"):
            try:
                ut = datetime.fromisoformat(data.get("unblocked_time"))
                d["unblocked_date"] = ut.strftime("%d/%m/%Y")
                d["unblocked_time"] = ut.strftime("%I:%M %p")
            except:
                d["unblocked_date"] = ""
                d["unblocked_time"] = ""
        else:
            d["unblocked_date"] = ""
           


        status = updated_map.get(donor_id, {}).get("status", "active")
        d["status"] = status

        if not d.get("status"):
            d["status"] = "active"    

        # Format Contact Numbers
        contact = str(d.get("contact_number", "")).strip()
        if contact and not contact.startswith("+"):
            d["contact_number"] = "+91 " + contact

        # Attach formatted date/time for display
        donor_id = str(d.get("donor_id"))
        if donor_id in updated_map:
            try:
                dt = datetime.fromisoformat(updated_map[donor_id].get("time"))
                d["updated_date"] = dt.strftime("%d/%m/%Y")
                d["updated_time"] = dt.strftime("%I:%M %p")
            except:
                d["updated_date"] = "N/A"
                d["updated_time"] = "N/A"
        else:
            d["updated_date"] = ""
            d["updated_time"] = ""

    return render_template(
        "admin_donors.html",
        donors=donors,
        cities=cities,
        selected_city=city,
        selected_blood=blood,
        filter_type=filter_type,
        updated_count=len(valid_recently_updated_ids)
    )


# --------------------------------------------------
#Admin Route (Filter Donors)
# --------------------------------------------------

@admin_app.route("/view-donors", methods=["GET","POST"])
def view_donors():

    df = pd.read_csv(CSV_FILE)

    # clean column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    cities = sorted(df["current_city"].dropna().unique())

    # 🔴 show all donors initially
    donors = df.to_dict("records")

    if request.method == "POST":

        city = request.form.get("city")
        blood = request.form.get("blood_group")

        filtered = df

        if city:
            filtered = filtered[filtered["current_city"] == city]

        if blood:
            filtered = filtered[filtered["blood_group"] == blood]

        donors = filtered.to_dict("records")

    return render_template(
        "view_donors.html",
        donors=donors,
        cities=cities
    )

#--------------------------------------------------------------
#----------------------DONOR STATUS----------------------------
#--------------------------------------------------------------

from datetime import datetime
import pandas as pd
from db_helper import save_to_db_from_df

@admin_app.route("/toggle-donor-status/<donor_id>")
def toggle_donor_status(donor_id):

    print("🔥 TOGGLE CALLED:", donor_id)
   
    if session.get("role") != "admin":
        return redirect("/admin-login")

    updates = get_persisted_updates()

    donor_id = str(donor_id).strip()

    if donor_id not in updates:
        updates[donor_id] = {}

    # INIT HISTORY
    if "history" not in updates[donor_id]:
        updates[donor_id]["history"] = []

    current_status = updates[donor_id].get("status", "active")
    now = datetime.now().isoformat()

    try:
        if current_status == "blocked":
            # ✅ UNBLOCK
            print("🟢 UNBLOCKING USER")

            updates[donor_id]["status"] = "active"
            updates[donor_id]["unblocked_time"] = now
            updates[donor_id].pop("blocked_time", None)

            print("💾 UPDATING DB TO ACTIVE")

            # 🔥 ADD THIS (DB UPDATE)
            row = pd.Series({
                "donor_id": donor_id,
                "status": "Active"
            })
            save_to_db_from_df(row)

            updates[donor_id]["history"].append({
                "action": "unblocked",
                "time": now
            })

        else:
            # ✅ BLOCK
            print("🔴 BLOCKING USER")

            updates[donor_id]["status"] = "blocked"
            updates[donor_id]["blocked_time"] = now
            updates[donor_id].pop("unblocked_time", None)

            print("💾 UPDATING DB TO BLOCKED")

            # 🔥 ADD THIS (DB UPDATE)
            row = pd.Series({
                "donor_id": donor_id,
                "status": "Blocked"
            })
            save_to_db_from_df(row)

            updates[donor_id]["history"].append({
                "action": "blocked",
                "time": now
            })

    except Exception as e:
        print("❌ DB ERROR:", e)

    # common update time
    updates[donor_id]["time"] = now

    save_persisted_updates(updates)

    return redirect("/admin-donors")


#--------------------------------------------------------------
#----------------------donor history-------------------------
#--------------------------------------------------------------

from datetime import datetime, timedelta
from flask import request, render_template, redirect, session

@admin_app.route("/donor-history/<donor_id>")
def donor_history(donor_id):

    if session.get("role") != "admin":
        return redirect("/admin-login")

    updates = get_persisted_updates()
    donor_id = str(donor_id)

    days_param = request.args.get("days")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    cutoff_start = None
    cutoff_end = None
    selected_days = None
    total_days = None

    # ✅ DAYS FILTER
    if days_param and days_param != "custom":
        try:
            selected_days = int(days_param)
            cutoff_start = datetime.now() - timedelta(days=selected_days)
        except:
            pass

    # ✅ CUSTOM RANGE (MAX 6 MONTHS)
    if days_param == "custom" and from_date and to_date:
        try:
            start = datetime.strptime(from_date, "%Y-%m-%d")
            end = datetime.strptime(to_date, "%Y-%m-%d")

            diff = (end - start).days

            if 0 <= diff <= 180:
                cutoff_start = start
                cutoff_end = end
                total_days = diff
        except:
            pass

    data = updates.get(donor_id, {})
    history = data.get("history", [])

    blocked_list = []
    unblocked_list = []

    for h in history:
        try:
            dt = datetime.fromisoformat(h.get("time"))

            if cutoff_start and dt < cutoff_start:
                continue
            if cutoff_end and dt > cutoff_end:
                continue

            item = {
                "date": dt.strftime("%d/%m/%Y"),
                "time": dt.strftime("%I:%M %p")
            }

            if h.get("action") == "blocked":
                blocked_list.append(item)
            else:
                unblocked_list.append(item)

        except:
            continue

    return render_template(
        "donor_history.html",
        donor_id=donor_id,
        blocked_list=blocked_list[::-1],
        unblocked_list=unblocked_list[::-1],
        selected_days=selected_days,
        from_date=from_date,
        to_date=to_date,
        total_days=total_days,
        selected_mode=days_param   # 🔥 important
    )

#--------------------------------------------------------------
#----------------------Forgot Password-------------------------
#--------------------------------------------------------------


@admin_app.route("/admin-forgot-password", methods=["GET","POST"])
def admin_forgot_password():

    if request.method == "POST":

        email = request.form["email"]

        if email != ADMIN_EMAIL:
            return render_template(
                "admin_forgot.html",
                error="Admin email not found"
            )

        send_otp(email)

        return redirect(
            url_for("admin_app.admin_verify_otp", email=email)
        )

    return render_template("admin_forgot.html")

#-------------------------------------------------------------------------
#---------------Verification Code Page------------------------------------
#-------------------------------------------------------------------------

@admin_app.route("/admin-verify-otp/<email>", methods=["GET","POST"])
def admin_verify_otp(email):

    if request.method == "POST":

        user_otp = request.form["otp"]

        result = validate_otp(email, user_otp)

        if result == "OK":
            return redirect(
                url_for("admin_app.admin_reset_password", email=email)
            )

        else:
            return render_template(
                "admin_otp_verify.html",
                error=result
            )

    return render_template("admin_otp_verify.html")

#---------------------------------------------------------------------------
#------------------------------------RESET PASSWORD-------------------------
#---------------------------------------------------------------------------

@admin_app.route("/admin-reset-password/<email>", methods=["GET","POST"])
def admin_reset_password(email):

    global ADMIN_PASSWORD

    if request.method == "POST":

        ADMIN_PASSWORD = request.form["password"]

        return redirect("/admin-login")

    return render_template("admin_reset_password.html")




# --------------------------------------------------
# ADMIN LOGOUT
# --------------------------------------------------

@admin_app.route("/admin-logout")
def admin_logout():

    session.pop("role",None)

    return redirect("/admin-login")