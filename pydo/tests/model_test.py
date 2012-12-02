from pydo.Model import User, List, Task, Tag
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from operator import attrgetter
from pydo.Model import Base


class TestUser:
    def setUp(self):
        engine = create_engine('sqlite:///:memory:', echo=True)
        
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        
    def test_can_create_user(self):
        new_user = User('TestUser')
        self.session.add(new_user)
        read_user = self.session.query(User).filter_by(display_name='TestUser').first()
        assert 'TestUser' == read_user.display_name

    def test_can_persist_user(self):
        new_user = User('SaveThisUser')
        new_user.oauth_token = "oauthtoken"
        new_user.oauth_secret = "secret"
        self.session.add(new_user)
        self.session.flush()
        find_user = self.session.query(User).filter_by(display_name='SaveThisUser').first()
        assert isinstance(find_user.id, int)
        assert find_user.display_name == "SaveThisUser"
        assert find_user.oauth_token == "oauthtoken"
        assert find_user.oauth_secret == "secret"
        
class TestList:
    def setUp(self):
        engine = create_engine('sqlite:///:memory:', echo=True)
        
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        
    def test_can_create_list_for_user(self):
        new_user = User('AUser')

        new_list = List('ListA')
        new_user.lists.append(new_list)
        self.session.add(new_user)
        self.session.flush()
        
        found_user = self.session.query(User).filter_by(display_name='AUser').first()
        assert len(found_user.lists) == 1

    def test_can_fetch_tasks_ordered(self):
        user = User('A User')
        list = List("List 1")
        user.lists.append(list)
        task = Task('1', datetime(2012,3,1))
        list.tasks.append(task)
        task = Task('2')
        list.tasks.append(task)
        task = Task('3', datetime(2012,5,1))
        list.tasks.append(task)
        self.session.add(user)
        self.session.commit()

        found_user = self.session.query(User).filter(User.id == user.id).first()
        found_tasks = found_user.lists[0].get_ordered_tasks_desc()

        assert found_tasks[0].description == "1"
        assert found_tasks[1].description == "3"
        assert found_tasks[2].description == "2"

    def test_can_fetch_tasks_filtered_by_tag_name(self):
        user = User('A User')
        list = List("List 1")
        user.lists.append(list)
        task = Task('A', datetime(2012,3,1))
        list.tasks.append(task)
        task = Task('B')
        tag = Tag.get(self.session, "TestTag")
        task.tags.append(tag)
        task.complete()
        list.tasks.append(task)
        task = Task('C', datetime(2012,5,1))
        tag = Tag.get(self.session, "AnotherTag")
        task.tags.append(tag)
        list.tasks.append(task)
        self.session.add(user)
        self.session.commit()

        found_user = self.session.query(User).filter(User.id == user.id).first()
        found_tasks = found_user.lists[0].get_ordered_tasks_desc(["TestTag", "AnotherTag"])
        assert len(found_tasks) == 2
        assert found_tasks[1].description == "B"
        assert found_tasks[1].completed == True
        assert found_tasks[0].description == "C"


class TestTask:
    def setUp(self):
        engine = create_engine('sqlite:///:memory:', echo=True)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        
    def test_can_create_task(self):
        user = User('A User')
        list = List("List 1")
        user.lists.append(list)
        task = Task('This is a test task', datetime.now())
        list.tasks.append(task)
        self.session.add(user)

        found_user = self.session.query(User).filter_by(display_name='A User').first()

        assert len(found_user.lists[0].tasks.all()) == 1
        assert found_user.lists[0].tasks[0].description  == 'This is a test task'

    def test_can_complete_task(self):
        user = User('A User')
        list = List("List 1")
        user.lists.append(list)
        task = Task('This is a test task', datetime.now())
        list.tasks.append(task)
        self.session.add(user)

        task.complete()
        self.session.commit()

        found_task = self.session.query(Task).filter(Task.id == task.id).first()
        assert found_task.completed == True


class TestTags:

    def setUp(self):
        engine = create_engine('sqlite:///:memory:', echo=True)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def test_can_add_tags(self):
        user = User('A User')
        list = List("List 1")
        user.lists.append(list)
        task = Task('This is a test task', datetime.now())
        list.tasks.append(task)
        tag_set = set(["Thing1", "Thing1", "Thing2"])
        for tag in tag_set:
            task.tags.append(Tag.get(self.session, tag))
        self.session.add(user)
        self.session.commit()

    def test_deleting_one_user_with_shared_tags_leaves_existing_tags(self):
        user = User('A User')
        list = List("List 1")
        user.lists.append(list)
        task = Task('This is a test task', datetime.now())
        list.tasks.append(task)
        tag_set = set(["Thing1", "Thing1", "Thing2"])
        for tag in tag_set:
            task.tags.append(Tag.get(self.session, tag))
        self.session.add(user)
        self.session.commit()

        user_b = User("B User")
        list = List("List 1")
        user.lists.append(list)
        task = Task("This is another task", datetime.now())
        list.tasks.append(task)
        tag_set = set(["Thing1", "Thing1", "Thing2"])
        for tag in tag_set:
            task.tags.append(Tag.get(self.session, tag))
        self.session.add(user_b)
        self.session.commit()

        del user_b
        self.session.commit()

        tags = self.session.query(Tag).all()
        assert len(tags) == 2

