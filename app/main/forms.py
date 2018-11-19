from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')

#def check_if_exists(table_name, field, field_value):
#    data = table_name.query.filter_by(field=field_value).first()
#    return data


class EnzymeForm(FlaskForm):
    name = StringField('Enzyme name (e.g. phosphofructokinase)', validators=[DataRequired()])
    acronym = StringField('Enzyme acronym (eg. PFK)', validators=[DataRequired()])
    isoenzyme = StringField('Isoenzyme (e.g. PFK1)', validators=[DataRequired()])
    ec_number = StringField('EC number', validators=[DataRequired()])

    gene_name = StringField('Encoding gene name', validators=[DataRequired()], id='inputOne')
    gene_bigg_id = StringField('Encoding gene bigg ID',  validators=[DataRequired()], id='inputTwo')

    submit = SubmitField('Submit')

class GeneForm(FlaskForm):
    name = StringField('Gene name (e.g. phosphofructokinase)', validators=[DataRequired()])
    bigg_id = StringField('Bigg Id (eg. g6p)', validators=[DataRequired()])

    submit = SubmitField('Submit')