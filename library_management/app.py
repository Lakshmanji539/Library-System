from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    available = db.Column(db.Boolean, default=True)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    issue_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)

# ✅ Admin login route
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # ✅ Updated credentials
        if username == 'Arjun' and password == 'arjun':
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/books', methods=['GET', 'POST'])
def books():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        db.session.add(Book(title=title, author=author))
        db.session.commit()
        flash('Book added successfully')
    all_books = Book.query.all()
    return render_template('books.html', books=all_books)

@app.route('/delete_book/<int:id>')
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted')
    return redirect(url_for('books'))

@app.route('/members', methods=['GET', 'POST'])
def members():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        db.session.add(Member(name=name, email=email))
        db.session.commit()
        flash('Member added successfully')
    all_members = Member.query.all()
    return render_template('members.html', members=all_members)

@app.route('/delete_member/<int:id>')
def delete_member(id):
    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    flash('Member deleted')
    return redirect(url_for('members'))

@app.route('/issue_return', methods=['GET', 'POST'])
def issue_return():
    members = Member.query.all()
    books = Book.query.filter_by(available=True).all()
    transactions = Transaction.query.all()

    if request.method == 'POST':
        member_id = request.form['member_id']
        book_id = request.form['book_id']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()

        if date < datetime.now().date():
            flash('Issue date cannot be in the past.')
            return redirect(url_for('issue_return'))

        transaction = Transaction(member_id=member_id, book_id=book_id, issue_date=date)
        db.session.add(transaction)

        book = Book.query.get(book_id)
        book.available = False

        db.session.commit()
        flash('Book issued successfully')
    return render_template('issue_return.html', members=members, books=books, transactions=transactions, today=datetime.now().date())

@app.route('/return_book/<int:id>')
def return_book(id):
    transaction = Transaction.query.get_or_404(id)
    transaction.return_date = datetime.now().date()

    book = Book.query.get(transaction.book_id)
    book.available = True

    db.session.commit()

    # Calculate late fine
    late_days = (transaction.return_date - transaction.issue_date).days - 7
    if late_days > 0:
        flash(f"Book returned with late fine. Late by {late_days} days.")
    else:
        flash("Book returned on time.")

    return redirect(url_for('issue_return'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
