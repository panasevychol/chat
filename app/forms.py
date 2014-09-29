from flask.ext.wtf import Form
from wtforms import TextField, BooleanField
from wtforms.validators import Required, Length

class LoginForm(Form):
    openid = TextField('openid', validators = [Required()])
    remember_me = BooleanField('remember_me', default = False)
    
class ChatRoomForm(Form):
    name = TextField('chat_room', validators = [Length(min = 1, max = 100)])