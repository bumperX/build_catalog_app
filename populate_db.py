from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBsession = sessionmaker(bind=engine)
session = DBsession()

category1 = Category(id=1, name='Snowboarding')
session.add(category1)
session.commit()

category2 = Category(id=2, name='Baseball')
session.add(category2)
session.commit()

category3 = Category(id=3, name='Golf')
session.add(category3)
session.commit()


item1 = CategoryItem(id=1, title='Snowboards',
                     description='snowboard', category_id=1)
session.add(item1)
session.commit()

item2 = CategoryItem(id=2, title='Boots', description='boot', category_id=1)
session.add(item2)
session.commit()

item3 = CategoryItem(id=3, title='Bindings',
                     description='binding', category_id=1)
session.add(item3)
session.commit()

item4 = CategoryItem(id=4, title='Googles',
                     description='google', category_id=1)
session.add(item4)
session.commit()

item5 = CategoryItem(id=5, title='Helmets',
                     description='helmet', category_id=1)
session.add(item5)
session.commit()

item6 = CategoryItem(id=6, title='Bats', description='bat', category_id=2)
session.add(item6)
session.commit()

item7 = CategoryItem(id=7, title='Gloves', description='glove', category_id=2)
session.add(item7)
session.commit()

item8 = CategoryItem(id=8, title='Cleats', description='cleat', category_id=2)
session.add(item8)
session.commit()

item9 = CategoryItem(id=9, title='Bags', description='bag', category_id=3)
session.add(item9)
session.commit()

item10 = CategoryItem(id=10, title='Grips', description='grip', category_id=3)
session.add(item10)
session.commit()


print "added menu items!"
