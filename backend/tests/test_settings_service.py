import pytest
from backend.services import settings_service
from backend.schemas.settings import UserSettingsCreate
from backend.models.settings import UserSettings

@pytest.fixture
def settings_in(test_user):
    return UserSettingsCreate(user_id=int(test_user.id), key="theme", value="dark")


def test_create_settings_with_check(db_session, settings_in):
    settings = settings_service.create_settings_with_check(db_session, settings_in)
    assert settings.key == settings_in.key
    assert settings.value == settings_in.value
    assert settings.user_id == settings_in.user_id
    # Should raise ValueError if duplicate
    with pytest.raises(ValueError):
        settings_service.create_settings_with_check(db_session, settings_in)


def test_get_settings_for_user(db_session, test_user, settings_in):
    settings_service.create_settings_with_check(db_session, settings_in)
    settings_list = settings_service.get_settings_for_user(db_session, int(test_user.id))
    assert isinstance(settings_list, list)
    assert any(s.key == settings_in.key for s in settings_list)


def test_update_settings_value(db_session, test_user, settings_in):
    settings_service.create_settings_with_check(db_session, settings_in)
    updated = settings_service.update_settings_value(db_session, int(test_user.id), settings_in.key, "light")
    assert updated.value == "light"


def test_delete_settings(db_session, test_user, settings_in):
    settings_service.create_settings_with_check(db_session, settings_in)
    deleted = settings_service.delete_settings(db_session, int(test_user.id), settings_in.key)
    assert deleted == 1
    # Should not find after delete
    value = settings_service.get_setting_value(db_session, int(test_user.id), settings_in.key)
    assert value is None


def test_get_setting_value(db_session, test_user, settings_in):
    settings_service.create_settings_with_check(db_session, settings_in)
    value = settings_service.get_setting_value(db_session, int(test_user.id), settings_in.key)
    assert value == settings_in.value
