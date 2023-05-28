# app.py
from flask import Flask, render_template, redirect, request, flash, abort, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.validators import Length, EqualTo
import random
import string
import smtplib
from email.mime.text import MIMEText
from flask_login import current_user 
from datetime import datetime
from flask_migrate import Migrate
import pytz



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'secret-key'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
warsaw_tz = pytz.timezone('Europe/Warsaw')
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(100))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    submit = SubmitField('Zaloguj się')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    confirm_password = PasswordField('potwierdź hasło', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Rejestracja')

class ResetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Restartuj hasło')

def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Obecne hasło', validators=[DataRequired()])
    new_password = PasswordField('Nowe hasło', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Potwierdź nowe hasło', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Zmień hasło')
    
class PostForm(FlaskForm):
    title = StringField('Tytuł', validators=[DataRequired()])
    content = TextAreaField('Treść', validators=[DataRequired()])
    submit = SubmitField('Zatwierdź')


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='posts')
    created_at = db.Column(db.DateTime, default=datetime.now(warsaw_tz))
    
class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now(warsaw_tz))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    author = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))
    post = db.relationship('Post', backref=db.backref('comments', lazy='dynamic'))

    def __init__(self, content, author, post):
        self.content = content
        self.author = author
        self.post = post

class CreatePostForm(FlaskForm):
    title = StringField('Tytuł', validators=[DataRequired()])
    content = TextAreaField('Treść', validators=[DataRequired()])
    submit = SubmitField('Stwórz post')

class CommentForm(FlaskForm):
    content = TextAreaField('Komentarz', validators=[DataRequired()])
    submit = SubmitField('Dodaj komentarz')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if not user:
            flash('Nieprawidłowy login lub hasło', 'error')
        elif user.check_password(form.password.data):
            login_user(user)
            flash('Zalogowano!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Nieprawidłowy login lub hasło', 'error')

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
            flash('Email jest już zajęty. Podaj inny wolny email.', 'danger')
        else:
            password = form.password.data
            if len(password) < 8 or password.isalpha() or password.isnumeric():
                flash('Hasło musi zawierać co najmniej 8 znaków (w tym litery i cyfrę).', 'danger')
                return redirect(url_for('register'))

            user = User(email=form.email.data)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Zarejestrowano. Zaloguj się.', 'success')  
            return redirect('/login')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.capitalize()}: {error}', 'danger')

    return render_template('register.html', form=form)




@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            new_password = generate_random_password()
            if len(new_password) < 8 or not any(char.isdigit() for char in new_password) or not any(
                    char.isalpha() for char in new_password):
                flash('Nowe hasło nie spełnia wymagań.', 'danger')
                return redirect(url_for('reset_password'))

            user.set_password(new_password)
            db.session.commit()

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
        if not current_user.check_password(form.current_password.data):
            flash('Obecne hasło jest nieprawidłowe.', 'danger')
            return redirect(url_for('change_password'))

        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Hasło zostało zmienione.', 'success')
 
        logout_user()
        
        return redirect(url_for('login'))
    
    return render_template('change_password.html', form=form)

def send_reset_password_email(email, new_password):

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'boardies.pomoc@gmail.com'
    smtp_password = 'jjtqmpjynnvwqmvw'

    message = MIMEText(f"Your new password is: {new_password}")
    message['Subject'] = 'Reset hasła'
    message['From'] = 'boardies.pomoc@gmail.com'
    message['To'] = email

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(message)
        server.quit()
        print("E-mail został wysłany")
    except Exception as e:
        print("Problem z wysłaniem maila:", str(e))

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
        flash('Utworzono post!', 'success')
        return redirect('/')
    return render_template('create_post.html', form=form)


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
        comment = Comment(content=form.content.data, author=current_user, post=post)  
        db.session.add(comment)
        db.session.commit()
        flash('Dodano komentarz', 'success')
    else:
        flash_errors(form)
    return redirect(url_for('home'))

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST', 'PUT'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403) 

    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Post został zaktualizowany', 'success')
        return redirect(url_for('home'))

    return render_template('edit_post.html', post=post, edit_form=form)


@app.route('/delete_post/<int:post_id>', methods=['GET', 'POST', 'DELETE'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)  
    
    if request.method == 'POST' or request.method == 'DELETE':
        comments= db.session.query(Comment).filter(Comment.post_id == post_id).all()
        for comment in comments:
            db.session.delete(comment)

        db.session.delete(post)
        db.session.commit()
        flash('Post został usunięty', 'success')
        return redirect(url_for('home'))
    
    return render_template('delete_post.html', post=post)

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Błąd z  {getattr(form, field).label.text}: {error}', 'danger')


@app.route('/api/posts', methods=['GET'])
def get_posts_api():

    posts = Post.query.all()
    posts_json = []
    for post in posts:
        posts_json.append({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author': post.author.email
        })

    return jsonify(posts_json)

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post_api(post_id):

    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    post_json = {
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'author': post.author.email
    }
    return jsonify(post_json)

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post_api(post_id):

    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    post.title = title
    post.content = content
    db.session.commit()

    post_json = {
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'author': post.author.email
    }
    return jsonify(post_json)


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post_api(post_id):

    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    db.session.delete(post)
    db.session.commit()


    return jsonify({'message': 'Post deleted successfully'})

@app.route('/api/users', methods=['POST'])
def create_user_api():

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    new_user = User(email=email, password_hash=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()

    user_json = {
        'id': new_user.id,
        'email': new_user.email,
        'password':new_user.password_hash
    }
    return jsonify(user_json), 201

@app.route('/api/users', methods=['GET'])
def get_users_api():

    users = User.query.all()
    users_json = []
    for user in users:
        users_json.append({
            'id': user.id,
            'email': user.email,
            'password':user.password_hash
        
        })

    return jsonify(users_json)

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_api(user_id):

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_json = {
        'id': user.id,
        'email': user.email
    }
    return jsonify(user_json)


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user_api(user_id):
 
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user.email = email
    user.password = generate_password_hash(password)
    db.session.commit()

    user_json = {
        'id': user.id,
        'name': user.name,
        'email': user.email
    }
    return jsonify(user_json)


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user_api(user_id):

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})


@app.errorhandler(Exception)
def handle_exception_(e):
    response = {
        'message': 'Wystąpił błąd',
        'error': str(e)
    }
    return jsonify(response), 500


@app.route('/')
@login_required
def home():
    posts =  Post.query.order_by(Post.created_at.desc()).all()
    comment_form = CommentForm()
    return render_template('home.html', posts=posts, comment_form=comment_form)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


