from app import db, app
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id              = db.Column(db.Integer, primary_key = True)
    name            = db.Column(db.String(30))
    email           = db.Column(db.String(64), unique=True, index=True)
    password_hash   = db.Column(db.String(128))
    wishlist        = db.relationship('Wishlist', backref='user', lazy='dynamic')
    
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return '<User %r>' % self.name
        
        
class Wishlist(db.Model):
    id              = db.Column(db.Integer, primary_key = True)
    title           = db.Column(db.String(200))
    description     = db.Column(db.String(5000))
    url             = db.Column(db.String(500))
    thumbnail       = db.Column(db.String(500))
    userid          = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return '<Item %r>' % self.title    


class Profile(db.Model):
    username    = db.Column(db.String(30),primary_key=True)
    userid      = db.Column(db.Integer)
    firstname   = db.Column(db.String(30))
    lastname    = db.Column(db.String(30))
    image       = db.Column(db.String(30))
    sex         = db.Column(db.String(6))
    age         = db.Column(db.Integer)
    profile_added_on = db.Column(db.DateTime)

    def __repr__(self):
        return'<Profile %r>' % self.username