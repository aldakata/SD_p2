from db import db, secret_key
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from flask_httpauth import HTTPBasicAuth
from flask import g, current_app


AVAILABLE_MONEY = 200
IS_ADMIN = 0
auth = HTTPBasicAuth()
class AccountsModel(db.Model):
    __tablename__ = 'accounts'
    username = db.Column(db.String(30), primary_key=True, unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    # 0 not admin/ 1 is admin
    is_admin = db.Column(db.Integer, nullable=False)
    available_money = db.Column(db.Integer)
    orders = db.relationship('OrdersModel', backref='orders', lazy=True)

    def json(self):
        return {"username":self.username, "available_money":self.available_money, "is_admin":self.is_admin}

    def save_to_db(self):
        if AccountsModel.query.get(self.username):
            db.session.commit()
            #raise UsernameTakenException("Username already taken, please choose another one")
        else:
            db.session.add(self)
            db.session.commit()

    def delete_from_db(self):
        if AccountsModel.query.get(self.username):
            db.session.delete(self)
            db.session.commit()
        else:
            raise Exception("Warning not in DB")

    def json(self):
        return {
            "username": self.username,
            "available_money": self.available_money,
            "is_admin": self.is_admin
        }

    @classmethod
    def find_by_username(cls, username):
        if username:
            return AccountsModel.query.filter_by(username=username).first()
        else:
            return None

    @classmethod
    def find_all(cls):
        return AccountsModel.query.all()

    def hash_password(self, password):
        self.password = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

    def generate_auth_token(self, expiration=600):
        s = Serializer(current_app.secret_key, expires_in=expiration)
        return s.dumps({'username': self.username})

    @classmethod
    def verify_auth_token(cls, token):
        s = Serializer(current_app.secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = AccountsModel.query.filter_by(username=data['username']).first()
        return user

    def __init__(self, username, available_money=AVAILABLE_MONEY, is_admin=IS_ADMIN):
        self.username = username
        self.available_money = available_money
        self.is_admin = is_admin




class UsernameTakenException(Exception):
    pass


@auth.verify_password
def verify_password(token, password):
    print("token{}".format(str(token)))
    acc = AccountsModel.verify_auth_token(token)
    if acc:
        g.user = acc
        print(g.user.username)
        return acc
    else:
        return None

@auth.get_user_roles
def get_user_roles(user):
    role = 'admin' if user.is_admin else 'user'
    print("role {}".format(user.json()))
    return role
