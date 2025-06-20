import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
from datetime import datetime, timedelta
from unittest import mock

import pytest
import toml

from imap_cleanup import cli

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


class DummyPrompt:
    def __init__(self, value):
        self.value = value

    def ask(self):
        return self.value


def test_get_imap_folders_success():
    mock_imap = mock.Mock()
    mock_imap_instance = mock_imap.return_value
    mock_imap_instance.login.return_value = ("OK", [b"Logged in"])
    mock_imap_instance.list.return_value = (
        "OK",
        [b'() "/" "INBOX"', b'() "/" "Archive"'],
    )
    mock_imap_instance.logout.return_value = ("OK", [])
    folders = cli.get_imap_folders(
        "server",
        993,
        "user",
        "pw",
        True,
        imap_class_ssl=mock_imap,
        imap_class=mock_imap,
    )
    assert folders == ["INBOX", "Archive"]


def test_get_imap_folders_error():
    mock_imap = mock.Mock()
    mock_imap_instance = mock_imap.return_value
    mock_imap_instance.login.return_value = ("OK", [b"Logged in"])
    mock_imap_instance.list.return_value = ("NO", [])
    mock_imap_instance.logout.return_value = ("OK", [])
    with pytest.raises(Exception):
        cli.get_imap_folders(
            "server",
            993,
            "user",
            "pw",
            True,
            imap_class_ssl=mock_imap,
            imap_class=mock_imap,
        )


def test_init_config_success(tmp_path):
    # Mock all user input und IMAP
    answers = iter(["mail.manitu.de", "993", "user"])

    def input_mock(prompt, **kwargs):
        return DummyPrompt(next(answers))

    select_mock = mock.Mock(return_value=mock.Mock(ask=lambda: "Yes"))
    checkbox_mock = mock.Mock(return_value=mock.Mock(ask=lambda: ["INBOX", "Archive"]))
    getpass_mock = mock.Mock(return_value="pw")
    get_folders_mock = mock.Mock(return_value=["INBOX", "Archive"])
    console_mock = mock.Mock()
    config_file = tmp_path / "config.toml"
    cli.init_config(
        config_file=str(config_file),
        input_func=input_mock,
        select_func=select_mock,
        checkbox_func=checkbox_mock,
        getpass_func=getpass_mock,
        get_folders_func=get_folders_mock,
        console=console_mock,
        toml_module=toml,
    )
    # Check file written
    assert config_file.exists()
    data = toml.load(config_file)
    for account in data["accounts"]:
        assert "mail.manitu.de" in account
        assert account["mail.manitu.de"]["server"] == "mail.manitu.de"
        assert account["mail.manitu.de"]["port"] == 993
        assert account["mail.manitu.de"]["user"] == "user"
        assert account["mail.manitu.de"]["password"] == "pw"
        assert account["mail.manitu.de"]["ssl"] is True
        assert "INBOX" in account["mail.manitu.de"]["folders"]
        assert "Archive" in account["mail.manitu.de"]["folders"]
    # Check console output
    assert console_mock.print.call_count > 0


def test_init_config_folder_error(tmp_path):
    answers = iter(["server", "993", "user"])

    def input_mock(prompt, **kwargs):
        return DummyPrompt(next(answers))

    select_mock = mock.Mock(return_value=mock.Mock(ask=lambda: "Yes"))
    checkbox_mock = mock.Mock(return_value=mock.Mock(ask=lambda: ["INBOX"]))
    getpass_mock = mock.Mock(return_value="pw")
    get_folders_mock = mock.Mock(side_effect=Exception("fail"))
    console_mock = mock.Mock()
    config_file = tmp_path / "config.toml"
    cli.init_config(
        config_file=str(config_file),
        input_func=input_mock,
        select_func=select_mock,
        checkbox_func=checkbox_mock,
        getpass_func=getpass_mock,
        get_folders_func=get_folders_mock,
        console=console_mock,
        toml_module=toml,
    )
    # Should not write file
    assert not config_file.exists()
    # Should print error
    assert console_mock.print.call_count > 0


def test_import_cli():
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
    import imap_cleanup.cli

    # Add more tests here
