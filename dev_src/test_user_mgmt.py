import pytest
import pickledb
import os, sys
from typing import Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from dev_src.pyroboxCore import config
import dev_src
from dev_src.user_mgmt import User, UserPermission

@pytest.fixture(scope="session", autouse=True)
def cleanup():
    from dev_src.user_mgmt import config
    # setup
    yield
    # teardown
    if os.path.exists(os.path.join(config.MAIN_FILE_dir, "test_users.db")):
        os.remove(os.path.join(config.MAIN_FILE_dir, "test_users.db"))
    # if os.path.exists(os.path.join(config.MAIN_FILE_dir, "users.db")):
    #     os.remove(os.path.join(config.MAIN_FILE_dir, "users.db"))
          

def test_mock_db(monkeypatch):
    from dev_src.user_mgmt import config
    test_user_db: pickledb.PickleDB = pickledb.load(
        os.path.join(config.MAIN_FILE_dir, "test_users.db"), True
    )
    monkeypatch.setattr("dev_src.user_mgmt.user_db", test_user_db)
    dev_src.user_mgmt.user_db.set("test_string", 8080)
    assert dev_src.user_mgmt.user_db.get("test_string") == 8080


def test_class_User_init(monkeypatch):
    from dev_src.user_mgmt import config
    test_user_db: pickledb.PickleDB = pickledb.load(
        os.path.join(config.MAIN_FILE_dir, "test_users.db"), True
    )
    monkeypatch.setattr("dev_src.user_mgmt.user_db", test_user_db)
    config.PASSWORD = "controlledPasswordSalt"
    demo_user_pw = "mydoghasfleas"
    demo_user_dn = "AliceTheAdmin"
    demo_user = User(
        username=demo_user_dn, permission=UserPermission(1), password=demo_user_pw
    )

    assert type(demo_user) == User
    assert type(demo_user.permission) == int
    assert demo_user.permission == 2
    assert type(demo_user.get_permissions()) == tuple
    assert type(demo_user.get_permissions()[0]) == UserPermission
    assert demo_user.username == demo_user_dn

    with pytest.raises(ValueError):
        User(username="non_exsistant", permission=UserPermission(1))


def test_class_User_lookup(monkeypatch):
    from dev_src.user_mgmt import config
    test_user_db: pickledb.PickleDB = pickledb.load(
        os.path.join(config.MAIN_FILE_dir, "test_users.db"), True
    )
    monkeypatch.setattr("dev_src.user_mgmt.user_db", test_user_db)
    demo_user_dn = "AliceTheAdmin"
    demo_user = User.get_user(demo_user_dn)
    assert type(demo_user) == User
    assert type(demo_user.permission) == int
    assert type(demo_user.get_permissions()) == tuple
    assert demo_user.username == demo_user_dn
    assert UserPermission(1) in demo_user.get_permissions()


def test_class_User_password(monkeypatch):
    from dev_src.user_mgmt import config
    test_user_db: pickledb.PickleDB = pickledb.load(
        os.path.join(config.MAIN_FILE_dir, "test_users.db"), True
    )
    monkeypatch.setattr("dev_src.user_mgmt.user_db", test_user_db)
    demo_user_dn = "AliceTheAdmin"
    demo_user_old_pw = "mydoghasfleas"
    demo_user_new_pw = "fleasdonthavedogs"
    demo_user = User.get_user(demo_user_dn)
    assert demo_user.check_creds(demo_user_old_pw)
    assert not demo_user.check_creds(demo_user_new_pw)
    demo_user.reset_pw(demo_user_old_pw, demo_user_new_pw)
    assert demo_user.check_creds(demo_user_new_pw)
    assert not demo_user.check_creds(demo_user_old_pw)
    assert demo_user.reset_pw("false_password", demo_user_new_pw) == 1


def test_class_User_getUser(monkeypatch):
    from dev_src.user_mgmt import config
    test_user_db: pickledb.PickleDB = pickledb.load(
        os.path.join(config.MAIN_FILE_dir, "test_users.db"), True
    )
    monkeypatch.setattr("dev_src.user_mgmt.user_db", test_user_db)
    demo_user_dn = "AliceTheAdmin"
    demo_user = User.get_user(demo_user_dn)
    assert type(User.get_user(username=demo_user_dn)) == User
    assert User.get_user(demo_user_dn).__dict__ == demo_user.__dict__
    if User.get_user(demo_user_dn):
        assert True
    if not User.get_user("wrong"):
        assert True


def test_class_User_permissions(monkeypatch):
    from dev_src.user_mgmt import config
    test_user_db: pickledb.PickleDB = pickledb.load(
        os.path.join(config.MAIN_FILE_dir, "test_users.db"), True
    )
    monkeypatch.setattr("dev_src.user_mgmt.user_db", test_user_db)
    demo_user_dn = "AliceTheAdmin"
    demo_user = User.get_user(demo_user_dn)
    demo_user.revoke(UserPermission(3))
    assert demo_user.permission == 2
    assert type(demo_user.get_permissions()) == tuple
    assert type(demo_user.get_permissions()[0]) == UserPermission
    assert UserPermission(1) in demo_user.get_permissions()

    demo_user.revoke(UserPermission(1))
    assert demo_user.permission == 0
    assert type(demo_user.get_permissions()) == tuple
    assert type(demo_user.get_permissions()[0]) == UserPermission
    assert UserPermission(0) in demo_user.get_permissions()

    demo_user.permit(UserPermission(1))
    demo_user.permit(UserPermission(3))
    assert demo_user.permission == 10
    assert type(demo_user.get_permissions()) == tuple
    assert type(demo_user.get_permissions()[0]) == UserPermission
    assert UserPermission(1) in demo_user.get_permissions()
    assert UserPermission(3) in demo_user.get_permissions()

    another_user = User(
        username="Charlie",
        permission=(UserPermission(3), UserPermission(5)),
        password="somep@ssword",
    )
    assert another_user.permission == 40
    assert type(another_user.get_permissions()) == tuple
    assert type(another_user.get_permissions()[0]) == UserPermission
    assert UserPermission(3) in another_user.get_permissions()
    assert UserPermission(5) in another_user.get_permissions()


def test_class_User_creds(monkeypatch):
    from dev_src.user_mgmt import config
    test_user_db: pickledb.PickleDB = pickledb.load(
        os.path.join(config.MAIN_FILE_dir, "test_users.db"), True
    )
    monkeypatch.setattr("dev_src.user_mgmt.user_db", test_user_db)
    user_bob = User("bob", UserPermission(0), "theP@ssword")
    assert user_bob.check_creds("theP@ssword")
    assert not user_bob.check_creds("NOTtheP@ssword")


def test_enum_UserPermission():
    for each in range(0, 6):
        assert UserPermission(each)

def test_adler32():
    test_value = "ab07e076-f1f6-11ed-a05b-0242ac120003"
    test_hash = "2956200217"
    from session_mgmt import adler32
    assert type(adler32(test_value)) == str
    assert adler32(test_value) == test_hash
    assert int(adler32(test_value)) == int(test_hash)
    from zlib import adler32 as zlib_adler32
    assert adler32(test_value) == str(zlib_adler32(test_value.encode()))
    assert int(adler32(test_value)) == int(zlib_adler32(test_value.encode()))

def test_session():
    from dev_src.user_mgmt import config
    from pickledb import PickleDB
    assert config.LOCALSESSION.user_db
    assert type(config.LOCALSESSION.user_db) == PickleDB