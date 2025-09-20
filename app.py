import os
from flask import Flask, render_template, request, session, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import hmac
import hashlib
import subprocess
import logging
from logging.handlers import RotatingFileHandler

# 1. --- APP INITIALIZATION & CONFIGURATION ---
app = Flask(__name__)
log_file = '/home/trackeco/launchpad/app.log'  # The log file will be in your project directory
log_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
log_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.INFO) # Set the level to INFO to capture everything

# Add the handler to your Flask app's logger
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO) # Also set the app's logger level

# Log a message right at startup to confirm the logger is working
app.logger.info('--- Flask App Starting Up ---')
# --- Configuration Section ---
# Use environment variables for secrets in production!
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET', 'a_very_secret_key_for_development')

# ==> Database configuration points to 'localhost'
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_NAME = os.environ.get('DB_NAME')
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASS}@localhost/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 2. --- INITIALIZE EXTENSIONS ---
db = SQLAlchemy(app)

# 3. --- DATABASE MODEL ---
# Note: The 'google_id' column has been removed.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False) # Not nullable anymore

    def __repr__(self):
        return f'<User {self.email}>'

# 4. --- ROUTE DEFINITIONS ---

# This command will run once before the first request to create the database table
@app.cli.command("init-db")
def init_db():
    """Clear the existing data and create new tables."""
    db.create_all()
    app.logger.info("Initialized the database.")

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

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        # Check if the user exists and the password hash matches the password provided
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['name'] = user.name
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    app.logger.info(f"DEBUG: Reached signup view with method: {request.method}")
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'error')
            return redirect(url_for('signup'))

        # --- THIS IS THE NEW DEBUGGING BLOCK ---
        try:
            # Hash the password for secure storage
            hashed_password = generate_password_hash(password, method='scrypt')

            new_user = User(name=name, email=email, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit() # This is the line that is likely failing

            # Log the new user in automatically
            session['user_id'] = new_user.id
            session['name'] = new_user.name
            
            app.logger.info(f"SUCCESS: User {email} created successfully.") # A success message for our log

            return redirect(url_for('dashboard'))

        except Exception as e:
            # If any error happens during the above 'try' block, it will be caught here
            db.session.rollback() # Roll back the transaction to keep the DB clean
            
            # This is the most important line for debugging.
            # It prints the exact database error to the console/log.
            app.logger.info(f"DATABASE ERROR ON SIGNUP: {e}")
            
            flash('A database error occurred. Please try again later.', 'error')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # You can retrieve the user from the database if you need more info
    # user = User.query.get(session['user_id'])
    return render_template('dashboard.html', name=session.get('name'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    # When running on your server, it's better to use a WSGI server like Gunicorn
    # For now, this is fine for testing.
    app.run(host='0.0.0.0', port=5000, debug=True)