from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)


db_path = os.path.join(os.path.dirname(__file__), 'instance', 'library.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)  # Ensure 'instance' folder exists
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    available = db.Column(db.Boolean, default=True)


with app.app_context():
    db.create_all()

@app.route('/')
def home():
    """Display all books."""
    books = Book.query.all()
    return render_template('base.html', book_list=books)

@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')

        if not title or not author:
            return "Error: Both Title and Author are required!", 400
        
        new_book = Book(title=title, author=author)
        db.session.add(new_book)
        db.session.commit()

        return redirect(url_for('home'))

    
    return render_template('add_book.html')


@app.route('/update/<int:book_id>')
def update(book_id):
    """Toggle book availability."""
    book = Book.query.get_or_404(book_id)
    book.available = not book.available  
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete/<int:book_id>')
def delete_book(book_id):
    """Delete a book by ID."""
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
