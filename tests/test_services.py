import services


def test_valid_phone():
    assert services.is_valid_contact("+79001234567")
    assert services.is_valid_contact("8 900 123-45-67")
    assert services.is_valid_contact("+7 (900) 123-45-67")
    assert services.is_valid_contact("79001234567")


def test_valid_username():
    assert services.is_valid_contact("@username")
    assert services.is_valid_contact("@user_123")
    assert services.is_valid_contact("@aaaaa")  # min length after @
    assert not services.is_valid_contact("@abcd")  # 4 символa — слишком коротко


def test_invalid_contact():
    assert not services.is_valid_contact("")
    assert not services.is_valid_contact("   ")
    assert not services.is_valid_contact("just text")
    assert not services.is_valid_contact("@ab")  # too short
    assert not services.is_valid_contact("+7")  # too short
    assert not services.is_valid_contact("89001234567extra!")
