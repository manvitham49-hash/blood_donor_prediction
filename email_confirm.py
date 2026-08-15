import yagmail

SENDER_EMAIL = "manvitham49@gmail.com"
APP_PASSWORD = "oszb brel fmtj vihy"

def send_registration_mail(to_email, donor_id, name):
    yag = yagmail.SMTP(SENDER_EMAIL, APP_PASSWORD)

    subject = "Blood Donor Registration Successful"
    content = [
        f"Hello {name},",
        "",
        f"🎉 You are successfully registered as a blood donor.",
        f"Your Donor ID is: {donor_id}",
        "",
        "Thank you for choosing to save lives ❤️"
    ]

    yag.send(to=to_email, subject=subject, contents=content)

    print("REGISTRATION EMAIL SENT!")
