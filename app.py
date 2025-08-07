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

# ─── App & Mail Setup ─────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('FLASK_SECRET', os.urandom(32)),
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=(
        "Launchpad.org Notifications",
        os.environ.get('MAIL_USERNAME')
    )
)
mail = Mail(app)

# ─── Fake Users ────────────────────────────────────────────────────────
FAKE_USERS = {
    "user@example.com": {
        "password": "password123",
        "name": "Demoman is gay"
    }
}


# ─── Logging Configuration ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ─── Utility: Async Email ─────────────────────────────────────────────────────────
def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            logger.info("Email sent successfully.")
        except Exception:
            logger.exception("Failed to send email.")

# ─── After-Request: Caching Headers ───────────────────────────────────────────────
@app.after_request
def add_cache_headers(response):
    response.cache_control.max_age = 300  # 5 minutes
    return response

# ─── Route: Favicon ───────────────────────────────────────────────────────────────
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

# ─── Route: GitHub Webhook ───────────────────────────────────────────────────────
@app.route('/git-webhook', methods=['POST'])
def git_webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        logger.warning("No signature header.")
        abort(403)

    sha_name, github_sig = signature.split('=', 1)
    if sha_name != 'sha256':
        logger.warning("Unsupported hash: %s", sha_name)
        abort(501)

    secret = os.environ.get('GITHUB_WEBHOOK_SECRET', '')
    computed = hmac.new(
        secret.encode(), msg=request.data,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed, github_sig):
        logger.warning("Signature mismatch.")
        abort(403)

    logger.info("Webhook verified; pulling latest code.")
    subprocess.Popen(['/home/ubuntu/launchpad/git-auto-pull.sh'])
    return '', 200

# ─── Route: Signup Form ───────────────────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        if not name or not email:
            logger.info("Rejected empty signup: %s", request.form)
            return jsonify(success=False, message="Missing required fields."), 400

        phone   = request.form.get('phone', 'Not provided')
        program = request.form.get('program', 'Not specified')
        message = request.form.get('message', 'No message was left.')

        html_body = render_template(
            'signup_email.html',
            name=name, email=email,
            phone=phone,
            program=program.replace('-', ' ').title(),
            message=message
        )

        msg = Message(
            subject=f"New Launchpad Signup: {name}",
            recipients=[app.config['MAIL_USERNAME']],
            html=html_body,
            reply_to=email
        )
        Thread(target=send_async_email, args=(app, msg), daemon=True).start()
        return jsonify(success=True, message="Thank you for signing up!"), 200

    return render_template('home.html')

# ─── Route: Login ─────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        logger.info("Login attempt: %s", email)

        user = FAKE_USERS.get(email)
        if user and user['password'] == password:
            session['email'] = email
            session['name']  = user['name']
            logger.info("Login success: %s", email)
            return redirect(url_for('dashboard'))

        logger.warning("Login failed: %s", email)
        return render_template('login.html', error="Invalid credentials.")

    return render_template('login.html')

# ─── Route: Dashboard & Logout ────────────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        return render_template('dashboard.html', name=session.get('name'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── Main Entrypoint ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run()  # In production: use Gunicorn or uWSGI
