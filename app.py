import os
import logging
import hmac
import hashlib
import subprocess
from threading import Thread

from flask import (
    Flask, render_template, request,
    jsonify, session, redirect,
    url_for, abort, send_from_directory
)
from flask_mail import Mail, Message

# 1. --- APP INITIALIZATION & CONFIGURATION ---
app = Flask(__name__)

# CRITICAL: A secret key is required by Flask to manage sessions securely.
# CHANGE THIS to a long, random, and secret string.
app.config.update(
    SECRET_KEY=os.environ.get('FLASK_SECRET', os.urandom(32)),
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER = ("Launchpad.org Notifications", os.environ.get('MAIL_USERNAME'))
)

GITHUB_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "default")
# This check warns you if email credentials aren't set, but allows the app to run.

mail = Mail(app)


# 2. --- FAKE USER DATABASE ---
# In a real application, you would connect to a database (e.g., SQLite, PostgreSQL).
# Passwords should ALWAYS be hashed, never stored in plain text.
FAKE_USERS = {
    "user@example.com": {
        "password": "password123",
        "name": "Demoman is gay"
    }
}


# 3. --- ASYNCHRONOUS EMAIL FUNCTION ---
def send_async_email(app, msg):
    """Sends an email in a background thread to avoid blocking the app."""
    with app.app_context():
        mail.send(msg)


# 4. --- ROUTE DEFINITIONS ---
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/git-webhook', methods=['POST'])
def git_webhook():
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    signature = request.headers.get('X-Hub-Signature-256')

    if not signature:
        abort(403)

    try:
        sha_name, github_signature = signature.split('=')
    except Exception as e:
        abort(403)

    if sha_name != 'sha256':
        abort(501)

    mac = hmac.new(secret.encode(), msg=request.data, digestmod=hashlib.sha256)
    your_signature = mac.hexdigest()


    if not hmac.compare_digest(your_signature, github_signature):
        abort(403)

    subprocess.Popen(['/home/ubuntu/launchpad/git-auto-pull.sh'])
    return 'Webhook verified.', 200

# The original route for the contact/signup form.
@app.route('/', methods=["GET", "POST"])
def index():
    # If the request is a POST, it's from the contact/signup form.
    if request.method == "POST":
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            if not name or not email:
                return jsonify({"success": False, "message": "Missing required fields."}), 400
            phone = request.form.get('phone', 'Not provided')
            program = request.form.get('program', 'Not specified')
            message_body = request.form.get('message', 'No message was left.')

            email_html_body = render_template(
                'signup_email.html',
                name=name, email=email,
                phone=phone, program=program, message=message_body
            )
            
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
        
        email = request.form.get('email')
        password = request.form.get('password')
        

        user = FAKE_USERS.get(email)
        # IMPORTANT: Check if user exists AND if the password matches.
        if user and user['password'] == password:
            # Store user info in the session to "log them in".
            session['email'] = email
            session['name'] = user['name']
            
            return redirect(url_for('dashboard'))
        else:
            # If details are incorrect, show an error on the login page.
            error = 'Invalid email or password. Please try again.'
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

@app.after_request
def add_cache_headers(response):
    # Cache pages for 5 minutes
    response.cache_control.max_age = 300
    return response

# 5. --- RUN THE APPLICATION ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
