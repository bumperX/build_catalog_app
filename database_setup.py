from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    """Create object User"""
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable way"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'picture': self.id
        }


class Category(Base):
    """Create object Category"""
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable way"""
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id
        }


class CategoryItem(Base):
    """Create object Item """
    __tablename__ = 'category_item'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    description = Column(String(250), nullable=False)

    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable way"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'user_id': self.user_id,
            'category_id': self.category_id
        }


engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)
