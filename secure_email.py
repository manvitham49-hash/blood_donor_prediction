import yagmail
import random
import time

# Store OTP in memory
OTP_STORE = {}

GMAIL_USER = "manvitham49@gmail.com"
GMAIL_APP_PASSWORD = "oszb brel fmtj vihy"

def send_otp(email):
    """Generate OTP and send via email"""

    otp = random.randint(100000, 999999)
    now = time.time()

    OTP_STORE[email] = {
        "otp": str(otp),
        "created": now,
        "attempts": 0,
        "locked_until": 0
    }

    try:
        yag = yagmail.SMTP(GMAIL_USER, GMAIL_APP_PASSWORD)
        yag.send(
            to=email,
            subject="Your OTP - Blood Donor Forgot Password",
            contents=f"Your OTP is: {otp}\n\nIt is valid for 5 minutes."
        )
        print("OTP sent:", otp)

    except Exception as e:
        print("Email sending error:", e)


def validate_otp(email, user_otp):
    """Validate OTP with expiry, attempts, and lock rules"""

    if email not in OTP_STORE:
        return "NO_OTP"

    data = OTP_STORE[email]
    now = time.time()

    # Check lock
    if now < data["locked_until"]:
        return "LOCKED"

    # Expired after 5 minutes (300 sec)
    if now - data["created"] > 300:
        return "EXPIRED"

    # Check attempts
    if data["attempts"] >= 5:
        data["locked_until"] = now + (30 * 60)  # lock for 30 minutes
        OTP_STORE[email] = data
        return "LOCKED"

    # OTP match
    if user_otp == data["otp"]:
        return "OK"

    # Invalid OTP
    data["attempts"] += 1
    OTP_STORE[email] = data
    return "INVALID"
