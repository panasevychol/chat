from gevent import monkey
from flask import render_template, flash, redirect, session, url_for, request, g, Flask, Response
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm, ChatRoomForm
from models import User, ROLE_USER, ROLE_ADMIN, ChatRoom

from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin

import sys
reload(sys)
sys.setdefaultencoding('utf8')

monkey.patch_all()

class ChatNamespace(BaseNamespace, BroadcastMixin):

    def initialize(self):
        self.logger = app.logger
        self.log("Socketio session started")

    def log(self, message):
        self.logger.info("[{0}] {1}".format(self.socket.sessid, message))

    def recv_connect(self):
        self.log("New connection")

    def recv_disconnect(self):
        self.log("Client disconnected")

    def on_join(self, email):
        self.log("%s joined chat" % email)
        self.session['email'] = email
        return True, email

    def on_message(self, message):
        self.log('got a message: %s' % message)
        self.broadcast_event_not_me("message",{ "sender" : self.session["email"], "content" : message})
        return True, message

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user
    g.search_form = ChatRoomForm()

@app.route('/')
@app.route('/chat')
@login_required
def chat():
    user = g.user
    rooms = ChatRoom.query.order_by(ChatRoom.id.desc())
    room_id = g.user.chat_room
    room_name = g.user.position.name
    return render_template('chat.html',
        title = 'Home',
        user = user,
        rooms = rooms,
        current_room = room_id,
        current_room_name = room_name)

@app.route('/login', methods = ['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for = ['nickname', 'email'])
    return render_template('login.html', 
        title = 'Sign In',
        form = form,
        providers = app.config['OPENID_PROVIDERS'])

@oid.after_login
def after_login(resp):    
    if ChatRoom.query.filter_by(name = 'general').first() is None:
        position = ChatRoom(name = 'general')
        db.session.add(position)
        db.session.commit()
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email = resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        position = ChatRoom.query.filter_by(name = 'general').first()
        user = User(nickname = nickname, email = resp.email, role = ROLE_USER, position = position)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('chat'))

@app.route('/manage_rooms', methods = ['GET', 'POST'])
@login_required
def manage_rooms():
    form = ChatRoomForm()    
    rooms = ChatRoom.query.order_by(ChatRoom.id.desc())
    empty_rooms = ChatRoom.query.filter_by(members = None)
    print empty_rooms
    if form.validate_on_submit():
        new_room_name = form.name.data
        if ChatRoom.query.filter_by(name = new_room_name).first() != None:
            flash('That room is already exists!')
        else:
            current_user = g.user
            new_room = ChatRoom(name = new_room_name)
            db.session.add(new_room)
            db.session.commit()
            flash('New room is created!')
        return redirect(url_for('manage_rooms'))

    return render_template('manage_rooms.html',
        form = form,
        rooms = rooms,
        empty_rooms = empty_rooms)

@app.route('/delete_room/<room_id>', methods = ['GET', 'POST'])
@login_required
def delete_room(room_id):
    current_room = ChatRoom.query.filter_by(id = room_id).first()
    form = ChatRoomForm()
    if form.validate_on_submit():
        db.session.delete(current_room)
        db.session.commit()
        flash('Your room sucsessfully deleted.')
        return redirect(url_for('manage_rooms'))
    else:
        form.name.data = current_room.name

    return render_template('delete_room.html',
        form = form)

@app.route('/room/<room_id>', methods = ['GET', 'POST'])
@login_required
def room(room_id):
    current_user = g.user
    current_user.chat_room = room_id
    db.session.add(current_user)
    db.session.commit()
    return redirect(url_for('chat'))

@app.route('/search', methods = ['POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('chat'))
    return redirect(url_for('search_results', query = g.search_form.name.data))

@app.route('/search_results/<query>')
@login_required
def search_results(query):
    results = ChatRoom.query.filter(ChatRoom.name.contains(query)).all()

    return render_template('search_results.html',
        query = query,
        results = results)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('chat'))

@app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    room = g.user.chat_room
    try:
        socketio_manage(request.environ, {'/'+str(room): ChatNamespace}, request)
    except:
        app.logger.error("Exception while handling socketio connection",
                         exc_info=True)
    return Response()

