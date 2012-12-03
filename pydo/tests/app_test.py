__author__ = 'jlon'

import os
import app
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydo.Model import Base
from pydo.Model import User

class TestPyDoApp:
    def setUp(self):


        app.app.config['TESTING'] = True
        app.app.config['DATABASE_URL'] = 'sqlite:///:memory:'
        self.app = app.app.test_client()
        app.init_db()
        user = User("TestUser")
        app.db_session.add(user)
        app.db_session.commit()



    def test_parse_tags_from_description(self):
            from app import filter_tokens

            description = "This is a description with @tag1 @anotherTag"
            description, token_list = filter_tokens(description)
            assert description == "This is a description with"
            assert len(token_list) == 2
            assert token_list[0] == "tag1"
            assert token_list[1] == 'anotherTag'

