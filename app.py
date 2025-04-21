from flask import *
import requests
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, validators, PasswordField, SubmitField ,SelectField,BooleanField
from wtforms.validators import DataRequired, Email 
import email_validator
from flask_session import Session
from model_training.model import get_recommendations


app=Flask(__name__)
bcrypt = Bcrypt(app)
mysql = MySQL(app)

app.config["SESSION_PERMANENT"] = False     # Sessions expire when browser closes
app.config["SESSION_TYPE"] = "filesystem"     # Store session data on the filesystem
Session(app)
 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'skincaredb'

app.secret_key="maitreyee"

class contactForm(FlaskForm): 
    name = StringField(label='Name', validators=[DataRequired()]) 
    email = StringField(label='Email', validators=[DataRequired(), Email(granular_message=True)]) 
    message = StringField(label='Message') 
    newsletter=BooleanField(label='Subscribe to our newsletter for skincare tips and exclusive offers')
    subject=SelectField(label="Subject",
                        validators=[DataRequired(message='please select a subject')], 
                         choices=[
                        ('','Select'),
                        ('Product Inquery','Product Inquery'),
                        ('Order Status','Order Status'),
                        ('Customer Support','Customer Support'),
                        ('Feedback','Feedback'),('Other','Other')])
    submit = SubmitField(label="Submit") 



@app.route('/')
def index():
    
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('aboutus.html')

@app.route('/register',methods=['GET','POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        print(f"Username: {username}, Password: {password}, Email: {email}")

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = % s', (username, ))
        users = cursor.fetchone()
        
        
        if users:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8') 
            cursor.execute('INSERT INTO users VALUES (NULL, % s, % s, % s)', (username,email, hashed_password, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
           
            session['loggedin'] = True
            session['id'] = users['userId']
            session['username'] = users['username']
            return redirect(url_for("index"))
        print(msg)
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
        print(msg)
        
    return render_template('register.html', msg = msg)


@app.route('/login',methods=['POST','GET'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        print(f"Username: {username}, Password: {password}")
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s ', (username,  ))
        users = cursor.fetchone()

        if users is None:
        # User not found in the database
            flash('User not found')
            return redirect(url_for('login'))

        print(users['password'])
        
        if users :
            stored_pass=users['password']
            print(f"Stored Hash: {stored_pass}")
            print(f"Entered Password: {password}")
            
            print(f"Hash Match: {bcrypt.check_password_hash(stored_pass, password)}")

            if bcrypt.check_password_hash(stored_pass.strip(), password):
                session['loggedin'] = True
                session['id'] = users['userId']
                session['username'] = users['username']
                msg = 'Logged in successfully !'
                flash(msg)
                print(msg)
                return redirect(url_for("index"))
            else:
                print('Incorrect password!!')
                flash('Incorrect password!!')
        else:
            msg = 'User doesn not exist!!'

        flash(msg)
    return render_template('login.html', msg = msg)


@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('index')) 

    

@app.route("/contact", methods=["GET", "POST"]) 
def contact(): 
    cform=contactForm() 
    if cform.validate_on_submit(): 
            name=cform.name.data
            email=cform.email.data
            message=cform.message.data
            subject=cform.subject.data
            newsletter=cform.newsletter.data
            print(f"Name:{name}, E-mail:{email}, message:{message}")
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO contact (Name, Email, Message,Subject,Subscribed) VALUES ( %s, %s, %s,%s,%s)',(name,email,message,subject,newsletter))
            mysql.connection.commit()
            flash("Form submitted successfully!")
            return redirect(url_for("index"))
    return render_template("contact.html",form=cform) 

@app.route('/model')
def model():
    if session.get('loggedin'):
        return render_template('model.html')
    else:
        flash('Please Login to access the Recommendation Model')
        return render_template('login.html')
    

@app.route('/recommend', methods=['POST'])
def recommend():
    skinType = request.form['user_skin_type']
    concern = request.form['concern']
    category = request.form['product_category']
    k=int(request.form['number'])
    print(skinType)
    print(concern)
    print(category)
    print(k)
    
    results = get_recommendations(skinType, concern, category,k)

    print(results)

    if results.empty:
        return render_template('model.html', prediction_text="No matching products found")
    
    products = results[['product_name', 'brand', 'price','product_href','picture_src']]  # Example fields
    return render_template('model.html', prediction_text="Here are your recommendations:", products=products.values.tolist())

if __name__ == "__main__":
    app.run(debug=True)