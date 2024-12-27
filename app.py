from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret_key'

# MySQL config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'jai1234'
app.config['MYSQL_DB'] = 'event'

mysql = MySQL(app)

# Ensure upload folder exists
UPLOADS = 'static/uploads'
os.makedirs(UPLOADS, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOADS

def init_db():
    cur = mysql.connection.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INT AUTO_INCREMENT PRIMARY KEY,
        uname VARCHAR(100),
        passwd VARCHAR(255)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS events (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ev_date DATE,
        title VARCHAR(255),
        total INT,
        brochure VARCHAR(255)
    )''')
    
    # Insert default admin user
    cur.execute("SELECT * FROM admin WHERE uname = %s", ('admin',))
    if not cur.fetchone():
        default_password = generate_password_hash('admin')
        cur.execute("INSERT INTO admin (uname, passwd) VALUES (%s, %s)", ('admin', default_password))
    
    mysql.connection.commit()
    cur.close()

db_initialized = False  # Flag to ensure setup runs only once

@app.before_request
def setup():
    global db_initialized
    if not db_initialized:
        init_db()
        db_initialized = True

@app.route('/')
def home():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM events")
    events = cur.fetchall()
    cur.close()
    return render_template('home.html', events=events)

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        uname = request.form['uname']
        passwd = request.form['passwd']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admin WHERE uname = %s", (uname,))
        admin = cur.fetchone()
        cur.close()

        if admin and check_password_hash(admin[2], passwd):
            session['admin'] = admin[1]
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')

    return render_template('admin_login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        ev_date = request.form['date']
        title = request.form['title']
        total = request.form['total']
        brochure = request.files['brochure']

        if brochure:
            b_path = os.path.join(app.config['UPLOAD_FOLDER'], brochure.filename)
            brochure.save(b_path)

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO events (ev_date, title, total, brochure) VALUES (%s, %s, %s, %s)",
                        (ev_date, title, total, brochure.filename))
            mysql.connection.commit()
            cur.close()

            flash('Event added', 'success')
        else:
            flash('Failed to upload brochure', 'danger')

    return render_template('admin_dashboard.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)
