import pytest
import pickledb
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dev_src.pyroboxCore import config
import dev_src
from dev_src.user_mgmt import User, UserPermission


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    # setup
    yield
    # teardown
    os.remove(os.path.join(config.MAIN_FILE_dir, "test_users.db"))


def test_mock_db(monkeypatch):
    test_user_db: pickledb.PickleDB = pickledb.load(
        os.path.join(config.MAIN_FILE_dir, "test_users.db"), True
    )
    monkeypatch.setattr("dev_src.user_mgmt.user_db", test_user_db)
    dev_src.user_mgmt.user_db.set("test_string", 8080)
    assert dev_src.user_mgmt.user_db.get("test_string") == 8080


def test_class_User_init(monkeypatch):
    test_user_db: pickledb.PickleDB = pickledb.load(
        os.path.join(config.MAIN_FILE_dir, "test_users.db"), True
    )
    monkeypatch.setattr("dev_src.user_mgmt.user_db", test_user_db)
    config.PASSWORD = "controlledPasswordSalt"
    demo_user_pw = "mydoghasfleas"
    demo_user_dn = "AliceTheAdmin"
    demo_user = User(
        username=demo_user_dn, permission=UserPermission(7), password=demo_user_pw
    )

    assert type(demo_user) == User
    assert type(demo_user.permission) == UserPermission
    assert demo_user.username == demo_user_dn
    assert demo_user.permission == UserPermission(7)


def test_class_User_lookup(monkeypatch):
    test_user_db: pickledb.PickleDB = pickledb.load(
        os.path.join(config.MAIN_FILE_dir, "test_users.db"), True
    )
    monkeypatch.setattr("dev_src.user_mgmt.user_db", test_user_db)
    demo_user_dn = "AliceTheAdmin"
    demo_user = User.get_user(demo_user_dn)
    assert type(demo_user) == User
    assert type(demo_user.permission) == UserPermission
    assert demo_user.username == demo_user_dn
    assert demo_user.permission == UserPermission(7)


def test_class_User_password(monkeypatch):
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


def test_class_User_permissions(monkeypatch):
    test_user_db: pickledb.PickleDB = pickledb.load(
        os.path.join(config.MAIN_FILE_dir, "test_users.db"), True
    )
    monkeypatch.setattr("dev_src.user_mgmt.user_db", test_user_db)
    demo_user_dn = "AliceTheAdmin"
    demo_user = User.get_user(demo_user_dn)
    demo_user.set_permissions(permission=40)  # invalid permission
    assert demo_user.permission == UserPermission(7)

    with pytest.raises(ValueError):
        demo_user.set_permissions(permission=UserPermission(40))  # invalid permission
    assert demo_user.permission == UserPermission(7)

    demo_user.set_permissions(permission=4)  # invalid permission
    demo_user.set_permissions(permission=UserPermission(4))  # valid permission
    assert demo_user.permission == UserPermission(4)

    assert type(User.get_user(username=demo_user_dn)) == User
    with pytest.raises(NameError):
        assert type(User.get_user("wrong"))
    assert User.get_user(demo_user_dn).__dict__ == demo_user.__dict__

    user_bob = User("bob", UserPermission(0), "theP@ssword")
    assert user_bob.check_creds("theP@ssword")
    assert not user_bob.check_creds("NOTtheP@ssword")
