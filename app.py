from flask import Flask, request, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'library.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    available = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user = db.relationship('User', backref=db.backref('books', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
@login_required
def home():
    books = Book.query.filter_by(user_id=current_user.id).all()
    return render_template('base.html', book_list=books, user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        if not title or not author:
            flash("Both Title and Author are required!", "danger")
            return redirect(url_for('add_book'))
        
        new_book = Book(title=title, author=author, user_id=current_user.id)
        db.session.add(new_book)
        db.session.commit()
        flash("Book added successfully!", "success")
        return redirect(url_for('home'))
    return render_template('add_book.html')

@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update_book(id):
    book = Book.query.get_or_404(id)
    

    if book.user_id != current_user.id:
        flash("You are not authorized to update this book!", "danger")
        return redirect(url_for('home'))
    

    book.available = not book.available
    db.session.commit()
    
    flash("Book availability updated successfully!", "success")
    return redirect(url_for('home'))



@app.route('/delete/<int:id>', methods=['GET'])
@login_required
def delete_book(id):
    book = Book.query.get_or_404(id)
    if book.user_id != current_user.id:
        flash("You are not authorized to delete this book!", "danger")
        return redirect(url_for('home'))
    
    db.session.delete(book)
    db.session.commit()
    flash("Book deleted successfully!", "success")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
