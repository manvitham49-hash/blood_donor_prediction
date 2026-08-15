from flask import Flask, render_template
from admin_routes import admin_app
from donor_routes import donor_app


# ----------------------------------------
# Flask Setup
# ----------------------------------------
app = Flask(__name__)
app.secret_key = "manvitha_secret"


# ----------------------------------------
# Register Blueprints
# ----------------------------------------
app.register_blueprint(admin_app)
app.register_blueprint(donor_app)


# ----------------------------------------
# Home Route (Login Options Page)
# ----------------------------------------
@app.route("/")
def home():
    return render_template("home.html")


# ----------------------------------------
# Run Flask
# ----------------------------------------
if __name__ == "__main__":
    app.run(debug=True)