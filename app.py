from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_mail import Mail, Message
from threading import Thread
import os
import traceback

# 1. --- APP INITIALIZATION & CONFIGURATION ---
app = Flask(__name__)

# CRITICAL: A secret key is required by Flask to manage sessions securely.
# CHANGE THIS to a long, random, and secret string.
app.config['SECRET_KEY'] = 'your-super-secret-key-change-me'

# Reads secure variables for email from environment variables (e.g., in cPanel).
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = ("Launchpad.org Notifications", os.environ.get('MAIL_USERNAME'))

# This check warns you if email credentials aren't set, but allows the app to run.
if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
    print("WARNING: MAIL_USERNAME or MAIL_PASSWORD environment variables are not set. Email sending will be disabled.")

mail = Mail(app)


# 2. --- FAKE USER DATABASE ---
# In a real application, you would connect to a database (e.g., SQLite, PostgreSQL).
# Passwords should ALWAYS be hashed, never stored in plain text.
FAKE_USERS = {
    "user@example.com": {
        "password": "password123",
        "name": "Demo User"
    }
}


# 3. --- ASYNCHRONOUS EMAIL FUNCTION ---
def send_async_email(app, msg):
    """Sends an email in a background thread to avoid blocking the app."""
    with app.app_context():
        try:
            mail.send(msg)
            print("--- Email sent successfully in background! ---", flush=True)
        except Exception as e:
            # Logs the full error to your server logs if sending fails.
            print(f"!!! FAILED TO SEND EMAIL: {e} !!!", flush=True)
            print(traceback.format_exc(), flush=True)


# 4. --- ROUTE DEFINITIONS ---

@app.route('/envcheck')
def envcheck():
    return {
        "MAIL_USERNAME": os.environ.get("MAIL_USERNAME"),
        "MAIL_PASSWORD_SET": bool(os.environ.get("MAIL_PASSWORD"))
    }

# The original route for the contact/signup form.
@app.route('/', methods=["GET", "POST"])
def index():
    # If the request is a POST, it's from the contact/signup form.
    if request.method == "POST":
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone', 'Not provided')
            program = request.form.get('program', 'Not specified')
            message_body = request.form.get('message', 'No message was left.')

            email_html_body = f"""
            <html><body>
                <h2>🚀 New Signup via Launchpad.org!</h2><hr>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email (for Reply-To):</strong> {email}</p>
                <p><strong>Phone:</strong> {phone}</p>
                <p><strong>Program Interest:</strong> {program.replace('-', ' ').title()}</p>
                <p><strong>Message:</strong></p><p><em>{message_body}</em></p>
            </body></html>
            """
            
            msg = Message(
                subject=f"New Launchpad Signup: {name}",
                recipients=[os.environ.get('MAIL_USERNAME')], # Sends email to you
                html=email_html_body,
                reply_to=email
            )
            # Starts the email sending in a separate thread.
            Thread(target=send_async_email, args=(app, msg)).start()
            return jsonify({"success": True, "message": "Thank you for signing up!"}), 200
        except Exception as e:
            print(f"!!! ERROR IN MAIN ROUTE: {e} !!!", flush=True)
            return jsonify({"success": False, "message": "An internal server error occurred."}), 500

    # If the request is a GET, just redirect to the login page.
    return render_template('home.html')


# The route for handling user login.
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, send them straight to the dashboard.
    if 'email' in session:
        return redirect(url_for('dashboard'))

    # If the form is being submitted.
    if request.method == 'POST':
        print("--- Login POST request received ---", flush=True) 
        
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Attempting login for email: {email}", flush=True)

        user = FAKE_USERS.get(email)
        # IMPORTANT: Check if user exists AND if the password matches.
        if user and user['password'] == password:
            # Store user info in the session to "log them in".
            session['email'] = email
            session['name'] = user['name']
            
            print("Login SUCCESS. Redirecting to dashboard.", flush=True)
            return redirect(url_for('dashboard'))
        else:
            # If details are incorrect, show an error on the login page.
            error = 'Invalid email or password. Please try again.'
            print("Login FAILED. Rendering login page with error.", flush=True)
            return render_template('login.html', error=error)
            
    # If it's a GET request, just show the login page.
    return render_template('login.html')


# The protected dashboard route.
@app.route('/dashboard')
def dashboard():
    # This is the security check: is the user logged in?
    if 'email' in session:
        user_name = session.get('name', 'User') # Get name from session
        return render_template('dashboard.html', name=user_name)
    
    # If not logged in, force them back to the login page.
    return redirect(url_for('login'))


# The route to log the user out.
@app.route('/logout')
def logout():
    # Clear the session dictionary to remove user data.
    session.clear()
    # Redirect back to the login page.
    return redirect(url_for('login'))


# 5. --- RUN THE APPLICATION ---
if __name__ == '__main__':
    # debug=True enables auto-reloading and provides detailed error pages.
    # Do NOT use debug=True in a production environment.
    app.run(debug=True)
