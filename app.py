from flask import Flask, render_template, request, redirect, url_for, session, flash
from extensions import db
from models import User, ConversionHistory
import requests

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

# Create database tables when the app starts
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('converter'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('converter'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
        else:
            new_user = User(email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/converter', methods=['GET', 'POST'])
def converter():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    result = None

    if request.method == 'POST':
        from_currency = request.form['from_currency']
        to_currency = request.form['to_currency']
        amount = float(request.form['amount'])

        # Fetch exchange rates from API
        response = requests.get(f"https://api.exchangerate-api.com/v4/latest/{from_currency}")
        data = response.json()

        if response.status_code == 200 and to_currency in data['rates']:
            rate = data['rates'][to_currency]
            result = round(amount * rate, 2)

            # Save conversion history in the database
            history_entry = ConversionHistory(
                user_id=user_id,
                from_currency=from_currency,
                to_currency=to_currency,
                amount=amount,
                result=result
            )
            db.session.add(history_entry)
            db.session.commit()
        else:
            flash("Error fetching exchange rates. Please try again.", "danger")

    return render_template('converter.html', result=result)

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conversions = ConversionHistory.query.filter_by(user_id=user_id).all()
    
    return render_template('history.html', conversions=conversions)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
