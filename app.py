from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel
import stripe
from flask_cors import CORS
from models import db  # Import the db from model.py
from chatbot import get_chatbot_response
import qrcode
from io import BytesIO
import base64
from apscheduler.schedulers.background import BackgroundScheduler
from flask import send_file
import uuid, os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import qrcode






app = Flask(__name__)
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:anji123@localhost/chatbot_db'   #try to host a postgresql databse for better and fast response
app.config['STRIPE_PUBLIC_KEY'] = 'your_stripe_public_key'
app.config['STRIPE_SECRET_KEY'] = 'your_stripe_secret_key'

# Initialize the app with the db
db.init_app(app)

babel = Babel(app)
CORS(app)

stripe.api_key = app.config['STRIPE_SECRET_KEY']

def get_locale():
    return session.get('locale', 'en')

babel.init_app(app, locale_selector=get_locale)

@app.context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)


@app.route('/set_locale/<locale>')
def set_locale(locale):
    session['locale'] = locale
    return redirect(request.referrer)

@app.route('/test_locale')
def test_locale():
    return f"Current locale: {get_locale()}"

@app.route('/logout')
def logout():
    # Logic to log out the user, e.g., clearing the session
    session.clear()
    return redirect(url_for('login'))  # Redirect to the login page or homepage

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/view')
def view():
    return render_template('view.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Process form data
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        # Here you can handle the form data, e.g., send an email, save to a database, etc.
        
        return "Thank you for your message!"  # Or redirect to a 'thank you' page
    return render_template('contact.html')



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        from models import User
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        from models import User
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('book_ticket'))
        else:
            return "Login failed"
    return render_template('login.html')


# In app.py - update the book_ticket function to include museum_name
@app.route('/book_ticket', methods=['GET', 'POST'])
def book_ticket():
    if request.method == 'POST':
        from models import Ticket
        import datetime
        
        age = int(request.form['age'])
        if age < 18:
            return "You must be 18 or older to book a ticket."
        
        # Parse the date string into a Python date object
        visit_date = datetime.datetime.strptime(request.form['museum_visit_date'], '%Y-%m-%d').date()
        
        ticket = Ticket(
            name=request.form['name'],
            age=age,
            email=request.form['email'],
            museum_name=request.form['museum_name'],  # Add this line
            museum_visit_date=visit_date,
            museum_visit_time=request.form['museum_visit_time'],
            user_id=session['user_id']
        )
        db.session.add(ticket)
        db.session.commit()
        return redirect(url_for('payment', ticket_id=ticket.id))
    return render_template('book_ticket.html')
    ticket_pdf = generate_ticket_pdf(name, museum, date, time)
    return send_file(ticket_pdf, as_attachment=True)




@app.route('/my_tickets')
def my_tickets():
    from models import Ticket
    user_id = session['user_id']
    tickets = Ticket.query.filter_by(user_id=user_id).all()
    return render_template('my_tickets.html', tickets=tickets)

@app.route('/delete_ticket/<int:ticket_id>', methods=['POST'])
def delete_ticket(ticket_id):
    from models import Ticket
    Ticket.query.filter_by(id=ticket_id).delete()
    db.session.commit()
    return redirect(url_for('my_tickets'))

# In app.py - modify the payment route
@app.route('/payment/<int:ticket_id>', methods=['GET'])
def payment(ticket_id):
    from models import Ticket
    ticket = Ticket.query.get_or_404(ticket_id)
    return render_template('payment.html', ticket=ticket)

# Add confirm_payment route
@app.route('/confirm_payment/<int:ticket_id>', methods=['POST'])
def confirm_payment(ticket_id):
    from models import Ticket
    import uuid
    
    ticket = Ticket.query.get_or_404(ticket_id)
    # Store transaction ID if needed
    # transaction_id = request.form['upi_transaction_id']
    
    # Generate unique ticket code
    ticket.ticket_code = 'MUS-' + str(uuid.uuid4().hex[:8]).upper()
    ticket.payment_status = True
    db.session.commit()
    
    # Here you would typically send email with ticket details
    
    return render_template('payment_success.html', ticket=ticket)



# Add these imports at the top of app.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add this function
def send_email_reminder(ticket):
    try:
        # Configure your email settings
        sender_email = "your_email@gmail.com"
        password = "your_app_password"  # Use app password for Gmail
        receiver_email = ticket.email
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Reminder: Your Museum Visit on {ticket.museum_visit_date.strftime('%d-%m-%Y')}"
        message["From"] = sender_email
        message["To"] = receiver_email
        
        # Create HTML content
        html = f"""
        <html>
        <body>
            <h2>Museum Visit Reminder</h2>
            <p>Dear {ticket.name},</p>
            <p>This is a friendly reminder about your upcoming visit to our museum.</p>
            <p><strong>Date:</strong> {ticket.museum_visit_date.strftime('%d-%m-%Y')}</p>
            <p><strong>Time:</strong> {ticket.museum_visit_time}</p>
            <p><strong>Ticket Code:</strong> {ticket.ticket_code}</p>
            <p>Please arrive 15 minutes before your scheduled time.</p>
            <p>We look forward to seeing you!</p>
        </body>
        </html>
        """
        
        # Add HTML content
        message.attach(MIMEText(html, "html"))
        
        # Send email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

# This function could be called from a scheduler
# For demonstration, we can add a manual reminder route
@app.route('/send_reminder/<int:ticket_id>')
def send_reminder(ticket_id):
    from models import Ticket
    ticket = Ticket.query.get_or_404(ticket_id)
    success = send_email_reminder(ticket)
    
    if success:
        return "Reminder sent successfully!"
    else:
        return "Failed to send reminder."




# Add this route to generate QR code
# In app.py - update the ticket_qr function
@app.route('/ticket_qr/<int:ticket_id>')
def ticket_qr(ticket_id):
    from models import Ticket
    from flask import send_file
    
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Create QR code with ticket info including museum name
    qr_data = f"ID: {ticket.id}\nName: {ticket.name}\nMuseum: {ticket.museum_name}\nDate: {ticket.museum_visit_date.strftime('%d-%m-%Y')}\nTime: {ticket.museum_visit_time}\nCode: {ticket.ticket_code}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to memory buffer
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    return send_file(buf, mimetype='image/png')


  
# Add admin route
@app.route('/admin')
def admin_dashboard():
    # In a real system, you'd check if the user is an admin
    from models import Ticket, User
    
    tickets = Ticket.query.order_by(Ticket.id.desc()).limit(10).all()
    total_tickets = Ticket.query.count()
    paid_tickets = Ticket.query.filter_by(payment_status=True).count()
    total_users = User.query.count()
    
    return render_template('admin_dashboard.html', 
                          tickets=tickets,
                          total_tickets=total_tickets,
                          paid_tickets=paid_tickets,
                          total_users=total_users)


@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if request.method == 'POST':
        data = request.get_json()
        user_message = data.get('message')
        bot_response = get_chatbot_response(user_message)
        return jsonify({"response": bot_response})
    else:
        return render_template('chatbot.html')  # Render the chatbot page if accessed via GET
    
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()



from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

def schedule_email_reminders():
    from models import Ticket
    tomorrow = datetime.now().date() + timedelta(days=1)
    tickets = Ticket.query.filter_by(museum_visit_date=tomorrow, payment_status=True).all()
    
    for ticket in tickets:
        send_email_reminder(ticket)

# Start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=schedule_email_reminders, trigger="interval", hours=24)
scheduler.start()


import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import uuid
import os

def generate_ticket_pdf(name, museum, date, time, filename=None):
    ticket_id = str(uuid.uuid4())[:8]
    qr = qrcode.make(f'TicketID: {ticket_id} | Name: {name} | Museum: {museum} | Date: {date} | Time: {time}')
    qr_path = 'static/qr_temp.png'
    qr.save(qr_path)

    if not filename:
        filename = f'static/ticket_{ticket_id}.pdf'

    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica", 16)
    c.drawString(100, 780, f"e-Ticket for {museum}")
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f"Name: {name}")
    c.drawString(100, 730, f"Date: {date}")
    c.drawString(100, 710, f"Time: {time}")
    c.drawString(100, 690, f"Ticket ID: {ticket_id}")
    c.drawImage(qr_path, 100, 550, width=150, height=150)
    c.save()

    os.remove(qr_path)  # Clean up the QR image after use
    return filename



if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
