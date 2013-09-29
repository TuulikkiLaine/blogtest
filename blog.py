import os

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

from flask.ext.login import LoginManager

from wtforms import Form, TextField, TextAreaField, PasswordField, validators, HiddenField

from flask_sqlalchemy import SQLAlchemy

import datetime

from string import replace, lower

import re

DEBUG = False
SECRET_KEY = 'vfaw)iul6d2@0b85$zy-^kdbd3i-7=ww_vtf%k9'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)

app.config.from_object(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

db = SQLAlchemy(app)

#relation table
tags = db.Table('tags',db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),db.Column('entry_id', db.Integer, db.ForeignKey('entry.id')))

class Entry(db.Model):
	
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(80))
	body = db.Column(db.Text)
	pub_date = db.Column(db.Date)
	taglist = db.relationship('Tag', secondary=tags, backref=db.backref('entry', lazy='dynamic'))
	def __init__(self, title, body, taglist, pub_date=None):
		self.title = title
		self.body = body
		if pub_date is None:
			pub_date = datetime.datetime.utcnow()
		self.pub_date = pub_date
		self.taglist = taglist
	def __repr__(self):
		return '<Entry %r>' % self.title
		
class Tag(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80))
	def __init__(self,name):
		self.name = name
	def __repr__(self):
		return '<Tag %r>' %self.name	

def tune_month(number):
	if number == '01': return 'January'
	if number == '02': return 'February'
	if number == '03': return 'March'
	if number == '04': return 'April'
	if number == '05': return 'May'
	if number == '06': return 'June'
	if number == '07': return 'July'
	if number == '08': return 'August'
	if number == '09': return 'September'
	if number == '10': return 'October'
	if number == '11': return 'November'
	if number == '12': return 'December'	
	
def get_navi():
	list_of_content = []
	for entry in Entry.query.all():
		list_of_content.append({
		'year':str(entry.pub_date)[0:4],
		'month':str(entry.pub_date)[5:7],
		'pub_date':entry.pub_date,
		'title':entry.title
		})	
	years = sorted(set(map(lambda x:x['year'],list_of_content)))
	final_list = []		
	for year in years:
		relevant_entries_of_year = filter(lambda x:x['year'] == year, list_of_content)
		relevant_months = sorted(set(map(lambda x:x['month'], relevant_entries_of_year)),reverse=True)
		months = []			
		for month in relevant_months:
			entries = sorted(filter(lambda x:x['year'] == year and x['month'] == month, list_of_content),reverse=True)
			d = {'name':tune_month(month),'entries':entries}
			months.append(d)
		d2 = {'name':year,'months':months}
		final_list.append(d2)
	return sorted(final_list,reverse=True)
	
class LoginForm(Form):
	username = TextField('username')
	password = PasswordField('password')
	def validate(self):
		global USERNAME, PASSWORD
		return self.username.data == USERNAME and self.password.data == PASSWORD

class AddEntryForm(Form):	
	title = TextField('Title', [validators.Required(),validators.Length(min=1,max=500)])
	body = TextAreaField('Entry')
	tags = TextField('Tags')

class EditEntryForm(Form):
	title = TextField('Title', [validators.Required(),validators.Length(min=1,max=500)])
	body = TextAreaField('Entry',)
	tags = TextField('Tags')	
	entry_id = HiddenField('entry_id',[validators.Required()])
	
class EditTagForm(Form):
	name = TextField('Name', [validators.Required(),validators.Length(min=1,max=50)])
	tag_id = HiddenField('tag_id',[validators.Required()])	
	
class SearchForm(Form):
	search = TextField('Search', [validators.Required()])	
	
	
@app.route("/")
def show_frontpage():
	return redirect(url_for('show_all_entries',page=1))

@app.route("/<page>")
def show_all_entries(page):
	navi = get_navi()	
	searchform = SearchForm()	
	try:
		page = int(page)
	except:
		return render_template('404.html', navi = navi, search=searchform), 404
	entries = Entry.query.order_by(Entry.pub_date.desc()).paginate(page,5,False)
	return render_template('index.html', entries=entries, navi=navi, search = searchform)

	
@app.route('/post/<title>')
def show_single_entry(title):
	entry = Entry.query.filter_by(title=title).first_or_404()
	navi = get_navi()	
	searchform = SearchForm()
	return render_template('single_entry.html',entry = entry,navi=navi,search=searchform)   
    
@app.route("/login", methods=["GET", "POST"])
def login():
	navi = get_navi()		
	error = None
	message= None
	print request.form
	if request.method == "POST":
		filledform = LoginForm(request.form)	
		print filledform.username.data
		print filledform.validate()
		if filledform.validate():
			session['logged_in'] = True
			return redirect(url_for('admin'))
		else:
			error = "Invalid usename or password"	
	searchform = SearchForm()	
	form = LoginForm()	
	return render_template('login.html', form=form,navi=navi,search=searchform, error=error)

@app.route('/logout')	
def logout():
	session.pop('logged_in', None)
	form = LoginForm()
	navi = get_navi()	
	flash('You were logged out')
	return redirect(url_for('login'))
	
@app.route('/admin', methods=["GET", "POST"])
def admin():
	entries = Entry.query.order_by(Entry.pub_date.desc())	
	form1 = AddEntryForm()
	edit_forms=[]
	for entry in entries:
		tags = ''
		for tag in entry.taglist:
			tags+=tag.name+','
		edit_forms.append(EditEntryForm(body=entry.body.replace("<br/>","\n"),title=entry.title,entry_id=entry.id,tags=tags))
	d = map(lambda x:{'entry':x[0],'form':x[1]}, zip(entries,edit_forms))	
	editable_tags = Tag.query.all()
	edit_tag_forms=[]
	for tag in editable_tags:
		edit_tag_forms.append(EditTagForm(name=tag.name,tag_id=tag.id))
	d2 = map(lambda x:{'tag':x[0],'form':x[1]}, zip(editable_tags,edit_tag_forms))	
	navi = get_navi()	
	searchform = SearchForm()
	return render_template('admin.html',session = session, form1 = form1, entries=d, tags=d2, navi=navi, search=searchform)

@app.route('/add_entry', methods=["GET", "POST"])	
def add_entry():
	form = AddEntryForm(request.form)
	if form.validate():	
		title = form.title.data
		body = form.body.data
		body = body.replace("\n", "<br/>")	
		comma_sep = str(request.values['tags'])
		comma_sep = comma_sep.replace(" ", "")
		comma_sep_to_list = comma_sep.split(',')
		taglist = []
		for tag in comma_sep_to_list:
			if len(list(Tag.query.filter_by(name=tag))) != 0 :
				for item in Tag.query.filter_by(name=tag):
					taglist.append(item)
			else:
				if not tag=='':
					taglist.append(Tag(tag))			
		db.session.add(Entry(title,body,taglist,pub_date=None))
		db.session.commit()
		flash ('Entry added successfully')
		return redirect(url_for('admin'))
	flash ('Title can not be empty')	
	return redirect(url_for('admin'))			

@app.route('/edit_entry', methods=["GET", "POST"])
def edit_entry():
	form = EditEntryForm(request.form)
	if form.validate():
		id = form.entry_id.data
		title = form.title.data
		body = form.body.data
		body = body.replace("\n", "<br/>")
		comma_sep = str(request.values['tags'])
		comma_sep = comma_sep.replace(" ", "")
		comma_sep_to_list = comma_sep.split(',')
		taglist = []
		for tag in comma_sep_to_list:
			if len(list(Tag.query.filter_by(name=tag))) != 0 :
				for item in Tag.query.filter_by(name=tag):
					taglist.append(item)
			else:
				if not tag=='':			
					taglist.append(Tag(tag))
		for entry in Entry.query.filter_by(id = id):
			entry.title = title
			entry.body = body
			entry.taglist = taglist
			db.session.commit()
		flash ('Entry edited successfully')	
		return redirect(url_for('admin'))	
	else:
		flash ('Title can not be empty')	
		return redirect(url_for('admin'))		
			

@app.route('/edit_tag',	methods=["GET", "POST"])
def edit_tag():
	form = EditTagForm(request.form)
	if form.validate():
		id = form.tag_id.data
		name = form.name.data
		for tag in Tag.query.filter_by(id=id):
			tag.name = name
			db.session.commit()
		flash ('Tag edited successfully')	
		return redirect(url_for('admin'))	
	else:
		flash ('Tag can not be empty')			
		return redirect(url_for('admin'))
			
@app.route('/delete_entry',	methods=["GET", "POST"])
def delete_entry():
	id = request.values['id']
	for entry in Entry.query.filter_by(id=id):
		if session.get('logged_in') and session['logged_in'] == True:
			db.session.delete(entry)
			db.session.commit()
		else:
			return redirect(url_for('login'))	
	flash ('Entry deleted successfully')		
	return redirect(url_for('admin'))	

@app.route('/delete_tag', methods=["GET","POST"])
def delete_tag():
	id = request.values['id']
	for tag in Tag.query.filter_by(id=id):
		if session.get('logged_in') and session['logged_in'] == True:
			db.session.delete(tag)
			db.session.commit()
		else:
			return redirect(url_for('login'))			
	flash ('Tag deleted successfully')		
	return redirect(url_for('admin'))			

@app.route('/result', methods=["GET","POST"])
def search():
	form = SearchForm(request.form)
	if form.validate():
		query = form.search.data.lower()
		entries = Entry.query.filter(Entry.title.ilike('%'+query+'%')).all()
		entries += Entry.query.filter(Entry.body.ilike('%'+query+'%')).all()
		entries = sorted(set(entries),key=lambda x:x.pub_date)		
		for entry in entries:
			search_terms = re.findall(r'(?i)'+query, entry.title)
			search_terms2 = re.findall(r'(?i)'+query, entry.body)
			for i in set(search_terms):
				entry.title = entry.title.replace(i,'<span style="color:red;">'+i+'</span>')
			for j in set(search_terms2):
				entry.body = entry.body.replace(j,'<span style="color:red;font-weight:bold;">'+j+'</span>')			
		navi = get_navi()
		searchform = SearchForm()
		return render_template('searchresult.html', entries=entries, navi=navi, search=searchform)
	else:
		return redirect(url_for('show_frontpage'))
	
@app.errorhandler(404)
def page_not_found(e):
	navi = get_navi()
	searchform = SearchForm()	
	return render_template('404.html', navi = navi, search=searchform), 404	
	
if __name__ == '__main__':
	app.run()	    
    