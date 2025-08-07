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

app.config.update(
    SECRET_KEY=os.environ.get('FLASK_SECRET', os.urandom(32)),
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=("Launchpad.org Notifications", os.environ.get('MAIL_USERNAME'))
)

GITHUB_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "default")
mail = Mail(app)

# 2. --- FAKE USER DATABASE ---
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
    except ValueError:
        abort(403)
    if sha_name != 'sha256':
        abort(501)
    mac = hmac.new(secret.encode(), msg=request.data, digestmod=hashlib.sha256)
    if not hmac.compare_digest(mac.hexdigest(), github_signature):
        abort(403)
    subprocess.Popen(['/home/ubuntu/launchpad/git-auto-pull.sh'])
    return 'Webhook verified.', 200

@app.route('/', methods=["GET", "POST"])
def index():
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
                recipients=[os.environ.get('MAIL_USERNAME')],
                html=email_html_body,
                reply_to=email
            )
            Thread(target=send_async_email, args=(app, msg)).start()
            return jsonify({"success": True, "message": "Thank you for signing up!"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": "An internal server error occurred."}), 500
    return render_template('home.html')

# *** NEW: Route for handling user signup ***
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'email' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not name or not email or not password:
            error = "All fields are required."
            return render_template('signup.html', error=error)

        if email in FAKE_USERS:
            error = "An account with this email already exists."
            return render_template('signup.html', error=error)
        
        # In a real app, HASH the password here!
        FAKE_USERS[email] = {"name": name, "password": password}
        
        # Log the new user in automatically
        session['email'] = email
        session['name'] = name
        
        return redirect(url_for('dashboard'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = FAKE_USERS.get(email)
        if user and user['password'] == password:
            session['email'] = email
            session['name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid email or password. Please try again.'
            return render_template('login.html', error=error)
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        user_name = session.get('name', 'User')
        return render_template('dashboard.html', name=user_name)
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.after_request
def add_cache_headers(response):
    response.cache_control.max_age = 300
    return response

# 5. --- RUN THE APPLICATION ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)