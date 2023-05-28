# app.py
from flask import Flask, render_template, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, TextAreaField
from flask import render_template, redirect, flash, request, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.validators import Length, EqualTo
import random
import string
import smtplib
from email.mime.text import MIMEText
from flask_login import current_user, login_required
from flask_login import logout_user
from datetime import datetime
from flask_migrate import Migrate
from flask import render_template






app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'secret-key'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Database models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(100))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ResetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset Password')

def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Obecne hasło', validators=[DataRequired()])
    new_password = PasswordField('Nowe hasło', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Potwierdź nowe hasło', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Zmień hasło')


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='posts')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    author = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))
    post = db.relationship('Post', backref=db.backref('comments', lazy='dynamic'))

    def __init__(self, content, author, post):
        self.content = content
        self.author = author
        self.post = post




class CreatePostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Create Post')


class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit Comment')



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html', form=form)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email address already exists. Please choose a different email.', 'danger')
        else:
            # Wymagania dotyczące hasła
            password = form.password.data
            if len(password) < 8 or password.isalpha() or password.isnumeric():
                flash('Password should be at least 8 characters long and contain both letters and numbers.', 'danger')
                return redirect(url_for('register'))

            user = User(email=form.email.data)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')  # Dodaj komunikat sukcesu
            return redirect('/login')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.capitalize()}: {error}', 'danger')

    return render_template('register.html', form=form)

from flask import render_template, redirect, flash, request, url_for

# ...

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Sprawdź istnienie użytkownika o podanym adresie e-mail
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Wygeneruj nowe hasło
            new_password = generate_random_password()

            # Sprawdź, czy nowe hasło spełnia wymagania
            if len(new_password) < 8 or not any(char.isdigit() for char in new_password) or not any(
                    char.isalpha() for char in new_password):
                flash('Nowe hasło nie spełnia wymagań.', 'danger')
                return redirect(url_for('reset_password'))

            # Zaktualizuj hasło użytkownika w bazie danych
            user.set_password(new_password)
            db.session.commit()

            # Wyślij e-mail z nowym hasłem
            if send_reset_password_email(user.email, new_password):
                flash('E-mail z instrukcjami do zresetowania hasła został wysłany.', 'success')
            else:
                flash('Wystąpił błąd podczas wysyłania wiadomości e-mail. Spróbuj ponownie później.', 'danger')

            return redirect(url_for('login'))
        else:
            flash('Podany adres e-mail nie istnieje.', 'danger')
    return render_template('reset_password.html', form=form)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Sprawdź poprawność obecnego hasła użytkownika
        if not current_user.check_password(form.current_password.data):
            flash('Obecne hasło jest nieprawidłowe.', 'danger')
            return redirect(url_for('change_password'))
        
        # Zaktualizuj hasło użytkownika
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Hasło zostało zmienione.', 'success')
        
        # Wyloguj użytkownika
        logout_user()
        
        return redirect(url_for('login'))
    
    return render_template('change_password.html', form=form)

def send_reset_password_email(email, new_password):
    # Konfiguracja serwera SMTP
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'boardies.pomoc@gmail.com'
    smtp_password = 'jjtqmpjynnvwqmvw'

    # Tworzenie wiadomości e-mail
    message = MIMEText(f"Your new password is: {new_password}")
    message['Subject'] = 'Reset Password'
    message['From'] = 'boardies.pomoc@gmail.com'
    message['To'] = email

    try:
        # Nawiązanie połączenia z serwerem SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)

        # Wysłanie wiadomości e-mail
        server.send_message(message)
        server.quit()

        print("E-mail sent successfully")
    except Exception as e:
        print("Error sending e-mail:", str(e))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect('/')
    return render_template('create_post.html', form=form)


# @app.route('/post/<int:post_id>', methods=['GET', 'POST'])
# def view_post(post_id):
#     post = Post.query.get_or_404(post_id)
#     comment_form = CommentForm()
#     if comment_form.validate_on_submit():
#         comment = Comment(content=comment_form.content.data, author=current_user, post=post)
#         db.session.add(comment)
#         db.session.commit()
#         flash('Comment added successfully!', 'success')
#         return redirect(url_for('view_post', post_id=post.id))
#     return render_template('view_post.html', post=post, comment_form=comment_form)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)



@app.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.content.data, author=current_user, post=post)  # Ustawienie autora komentarza
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully', 'success')
    else:
        flash_errors(form)
    return redirect(url_for('home'))



def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Error in the {getattr(form, field).label.text}: {error}', 'danger')




@app.route('/')
def home():
    # Pobierz listę postów
    posts = Post.query.all()

    # Utwórz formularz komentarza
    comment_form = CommentForm()

    return render_template('home.html', posts=posts, comment_form=comment_form)







# Run the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


