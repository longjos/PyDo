__author__="jlon"
__date__ ="$Dec 1, 2012 1:53:12 PM$"


from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# Table definition used to relate tags to tasks
tag_association = Table('tag_association', Base.metadata,
    Column('tag_id', Integer, ForeignKey('tag.id')),
    Column('task_id', Integer, ForeignKey('tasks.id'))
)

class User(Base):
    """ Model of a user

    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key = True)
    display_name = Column(String)
    oauth_token = Column(String(200))
    oauth_secret = Column(String(200))
    
    def __init__(self, display_name):
        self.display_name = display_name
        
class List(Base):
    """ A user created list of tasks

    """
    __tablename__ = 'lists'
    
    id = Column(Integer, primary_key = True)
    list_title = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    user = relationship("User", backref=backref('lists', order_by=id))
    
    def __init__(self, list_title):
        self.list_title = list_title
        
    def __repr__(self):
        return "<List('%s')>" % self.list_title

    def get_ordered_tasks_desc(self, filter_tags = None):
        """ Return a list of tasks contained by this list instance ordered by due date.
            Closest due date first. Tasks with no due date are moved to the end of the list
        :param: list of tags to filter by
        :return: list of sorted tasks

        """
        def fix_due_date(task_under_test):
            return task_under_test.date_due or datetime(3000, 1, 1)

        if filter_tags:
            relevant_tasks = self.tasks.join("tags").filter(Tag.name.in_(filter_tags)).all()
        else:
            relevant_tasks = self.tasks.all()

        sorted_tasks = sorted(relevant_tasks, key=fix_due_date, reverse = False)
        return sorted_tasks

class Task(Base):
    """ A user created Task.

    """
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key = True)
    description = Column(String(200))
    date_due = Column(DateTime)
    completed = Column(Boolean)
    
    list_id = Column(Integer, ForeignKey('lists.id'))
    list = relationship("List", backref=backref('tasks', lazy="dynamic", order_by=date_due))

    tags = relationship("Tag", secondary=tag_association, backref='tasks')

    def __init__(self, description, date_due = None):
        self.description = description
        self.date_due = date_due

    def __repr__(self):
        return "<Task('%s')>" % self.description

    def complete(self):
        """ Mark this instance complete
        :return: None

        """
        self.completed = True

class Tag(Base):
    """ A shared Tag used for categorizing Tasks and searching

    """
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, unique=True)

    def __init__(self, name):
        self.name = name

    # Factory method. If there is already a tag, use it, otherwise return a new instance
    @staticmethod
    def get(session, name):
        """ Find any existing tag by this name and return an instance of it.
            If none exists, create a new instance with the provided name

        :param session: SQLAlchemy Session to DB
        :param name: Name of the tag to return or create
        :return: Tag
        """
        existing_tag = session.query(Tag).filter(Tag.name == name).first()
        if not existing_tag:
            return Tag(name)
        return existing_tag

def init_db(engine):
    """ If the db is not setup, call this from a console to set it up

    """
    Base.metadata.create_all(bind=engine)
