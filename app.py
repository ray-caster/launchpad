import os
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# 1. --- APP INITIALIZATION & CONFIGURATION ---
app = Flask(__name__)

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
@app.before_first_request
def create_tables():
    db.create_all()

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
            hashed_password = generate_password_hash(password, method='sha256')

            new_user = User(name=name, email=email, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit() # This is the line that is likely failing

            # Log the new user in automatically
            session['user_id'] = new_user.id
            session['name'] = new_user.name
            
            print(f"SUCCESS: User {email} created successfully.") # A success message for our log

            return redirect(url_for('dashboard'))

        except Exception as e:
            # If any error happens during the above 'try' block, it will be caught here
            db.session.rollback() # Roll back the transaction to keep the DB clean
            
            # This is the most important line for debugging.
            # It prints the exact database error to the console/log.
            print(f"DATABASE ERROR ON SIGNUP: {e}")
            
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