from blog import db,Entry,Tag

db.create_all()

'''
import datetime

testentry8 = Entry("Testing testing testing","jeodgjbsd",Tag.query.all(),pub_date=datetime.date(2013,3,28))

db.session.add(testentry8)

db.session.commit()

for item in Tag.query.filter_by(name='apinat'):
	db.session.delete(item)
	
db.session.commit()	



'''