__author__ = 'jlon'


def test_parse_tags_from_description():
    from app import filter_tokens

    description = "This is a description with @tag1 @anotherTag"
    description, token_list = filter_tokens(description)
    assert description == "This is a description with"
    assert len(token_list) == 2
    assert token_list[0] == "tag1"
    assert token_list[1] == 'anotherTag'
