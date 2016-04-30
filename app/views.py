"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/

This file creates your application.
"""

from app import app, auth, db, thumbnailer, emailscript
from app.models import User, Wishlist, Profile
from flask import render_template, request, redirect, url_for, flash, g, jsonify, abort
from datetime import datetime, timedelta
import jwt
import base64
import os

from functools import wraps
from flask import Flask, request, jsonify, _request_ctx_stack
from werkzeug.local import LocalProxy
from flask.ext.cors import cross_origin


current_user = LocalProxy(lambda: _request_ctx_stack.top.current_user)

def authenticate(error):
  resp = jsonify(error)

  resp.status_code = 401

  return resp

def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    auth = request.headers.get('Authorization', None)
    if not auth:
      return authenticate({'code': 'authorization_header_missing', 'description': 'Authorization header is expected'})

    parts = auth.split()

    if parts[0].lower() != 'bearer':
      return {'code': 'invalid_header', 'description': 'Authorization header must start with Bearer'}
    elif len(parts) == 1:
      return {'code': 'invalid_header', 'description': 'Token not found'}
    elif len(parts) > 2:
      return {'code': 'invalid_header', 'description': 'Authorization header must be Bearer + \s + token'}

    token = parts[1]
    try:
         payload = jwt.decode(token, 'listen-this-is-a-secret-so-do-not-say-anything')
         g.current_user = payload
    except jwt.ExpiredSignature:
        return authenticate({'code': 'token_expired', 'description': 'token is expired'})
    except jwt.DecodeError:
        return authenticate({'code': 'token_invalid_signature', 'description': 'token signature is invalid'})
    
    _request_ctx_stack.top.current_user = user = payload
    return f(*args, **kwargs)

  return decorated


###
# Routing for your application.
###
@app.route('/')
def home():
    return render_template('index.html')

    
@app.route('/api/user/register', methods=['POST'])
@cross_origin(headers=['Content-Type', 'Authorization'])
def new_user():
    name        = request.form.get('name')
    email       = request.form.get('email')
    password    = request.form.get('password')
    
    if name is None or email is None or password is None:
        return jsonify({"error":1, "data":{}, "message":"All fields are required."})
    
    if db.session.query(User).filter_by(email=email).first() is not None:
        return jsonify({"error":2, "data":{}, "message":"This email is already linked to an account."})
    
    user = User(name=name, email=email, password=password)
    
    db.session.add(user)
    db.session.commit()
    
    response = {}
    response['error'] = None
    response['data'] = {}
    response['data']['token']   = get_auth_token(user.id,name,email)
    response['data']['expires'] = datetime.utcnow() + timedelta(days=1)
    response['data']['user']    = {"_id":user.id, "email":email, "name":name}
    response['message'] = "Success"
    
    return jsonify(response)
    
    
@app.route('/api/token')
def get_auth_token(id, name, email):
    token = jwt.encode({'_id': id, 'name':name, 'email':email, 'exp':datetime.utcnow() + timedelta(days=1)}, 'listen-this-is-a-secret-so-do-not-say-anything', algorithm='HS256')
    return token

    
@app.route('/api/user/login', methods=['POST'])
@cross_origin(headers=['Content-Type', 'Authorization'])
def login():
    email       = request.form.get('email')
    password    = request.form.get('password')
    
    if email is None or password is None:
        return jsonify({"error":1,"data":{},"message":"All fields are required"})
        
    user = db.session.query(User).filter_by(email = email).first()
    if user is not None and user.verify_password(password):
        response = {}
        response['error']           = None
        response['data']            = {}
        response['data']['token']   = get_auth_token(user.id,user.name,email)
        response['data']['expires'] = datetime.utcnow() + timedelta(days=1)
        response['data']['user']    = {"_id":user.id, "email":email, "name":user.name}
        response['message']         = "Success"
        
        return jsonify(response)
    
    return jsonify({"error":1,"data":{},"message":"Incorrect email or password"})
    
@app.route('/api/user', methods=['GET'])
@requires_auth
def get_user():
    response = {}
    response['error']           = None
    response['data']            = {}
    response['data']['user']    = g.current_user
    response['message']         = "Success"
    
    return jsonify(response)

@app.route('/api/user/<int:id>/wishlist', methods=['POST','GET'])
@cross_origin(headers=['Content-Type', 'Authorization'])
@requires_auth
def wishlist(id):
    if request.method == 'POST':
        title       = request.form.get('title')
        description = request.form.get('description')
        url         = request.form.get('url')
        thumbnail   = request.form.get('thumbnail')
        
        if title is None or description is None or url is None or thumbnail is None:
            return jsonify({"errors":1, "data":{}, "message":"All fields are required."})
        
        item = Wishlist(title=title, description=description, url=url, thumbnail=thumbnail, userid=id)
        
        db.session.add(item)
        db.session.commit()
        
        wishlistItems = db.session.query(Wishlist).filter_by(userid=id).all()
        if wishlistItems is None:
            return jsonify({"errors":2, "data":{}, "message":"No such wishlist exist."})
        
        wishes = []    
        for wish in wishlistItems:
            wishes.append({"title":wish.title, "description":wish.description, "url":wish.url, "thumbnail":wish.thumbnail})
        
        response = {}
        response['error']           = None
        response['data']            = {}
        response['data']['wishes']  = wishes
        response['message']         = "Your wish was successfully added!"
        return jsonify(response)
        
    else:
        wishlistItems = db.session.query(Wishlist).filter_by(userid=id).all()
        if wishlistItems is None:
            return jsonify({"errors":1, "data":{}, "message":"No such wishlist exist."})
        
        wishes = []    
        for wish in wishlistItems:
            wishes.append({"title":wish.title, "description":wish.description, "url":wish.url, "thumbnail":wish.thumbnail})
        
        response = {}
        response['error']           = None
        response['data']            = {}
        response['data']['wishes']  = wishes
        response['message']         = "Success"
        return jsonify(response)
    
@app.route('/api/user/<int:id>/wishlist/share', methods=['POST'])
@cross_origin(headers=['Content-Type', 'Authorization'])
@requires_auth
def share(id):
    emails = []
    emails.append(request.form.get('email1'))
    emails.append(request.form.get('email2'))
    emails.append(request.form.get('email3'))
    emails.append(request.form.get('email4'))
    emails.append(request.form.get('email5'))
    
    user = db.session.query(User).filter_by(id = id).first()
    
    for email in emails:
        if email:
            emailscript.sendemail("Friend",email,"{} just shared a wishlist!".format(user.name),"Find the wishlist here.\nhttps://wishlist-tonitiffy-1.c9users.io/#/user/{}/wishlist/shared_view".format(id)) 
    response = {}
    response['error']           = None
    response['data']            = {}
    response['data']['emails']  = emails
    response['message']         = "Wishes shared with friends and family!"
    return jsonify(response)
    
    
@app.route('/api/user/<int:id>/wishlist/shared', methods=['GET'])
@cross_origin(headers=['Content-Type', 'Authorization'])
def shared(id):
    user = db.session.query(User).filter_by(id = id).first()
    wishlistItems = db.session.query(Wishlist).filter_by(userid=id).all()
    if wishlistItems is None or user is None:
        return jsonify({"errors":1, "data":{}, "message":"No such wishlist exist."})
    
    wishes = []    
    for wish in wishlistItems:
        wishes.append({"title":wish.title, "description":wish.description, "url":wish.url, "thumbnail":wish.thumbnail})
    
    response = {}
    response['error']                   = None
    response['data']                    = {}
    response['data']['wishes']          = wishes
    response['data']['user']            = {}
    response['data']['user']['name']    = user.name
    response['message']                 = "Success"
    return jsonify(response)    
    
@app.route('/api/thumbnail/process',methods=['GET'])
@cross_origin(headers=['Content-Type', 'Authorization'])
def processThumbnail():
    url = request.args.get('url')
    response = thumbnailer.get_data(url)
    return jsonify(response)
    
