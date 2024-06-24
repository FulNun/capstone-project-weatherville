from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UserPreferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100))
    zip_code = db.Column(db.String(10))