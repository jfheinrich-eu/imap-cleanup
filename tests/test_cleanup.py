import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))
import imap_cleanup.cli as cli  # Import the cli module from the parent directory
import pytest
import toml
from unittest import mock
from datetime import datetime, timedelta, timezone


@pytest.fixture
def fake_config(tmp_path):
    config = {
        'accounts': [
            {
                'server': 'imap.example.com',
                'port': 993,
                'user': 'user',
                'password': 'pw',
                'ssl': True,
                'folders': {
                    'INBOX': {'purge': True, 'retention_days': 30},
                    'Archive': {'purge': False,'retention_days': 30}
                }
            }
        ]
    }
    config_path = tmp_path / 'config.toml'
    with open(config_path, 'w') as f:
        toml.dump(config, f)
    return config_path


@mock.patch('imap_cleanup.cli.console')
@mock.patch('imap_cleanup.cli.tqdm')
@mock.patch('imap_cleanup.cli.imaplib.IMAP4_SSL')
def test_cleanup_deletes_old_mails(mock_imap, mock_tqdm, mock_console, fake_config, monkeypatch):
    # Patch config file path
    monkeypatch.setattr(cli, 'CONFIG_FILE', str(fake_config))
    # Setup fake IMAP
    instance = mock_imap.return_value
    instance.login.return_value = ('OK', [b'Logged in'])
    instance.select.return_value = ('OK', [b''])
    instance.search.return_value = ('OK', [b'1 2 3'])
    # Setze das Datum der alten Mails auf 40 Tage in der Vergangenheit
    old_date = (datetime.now(timezone.utc) - timedelta(days=40)).strftime('%a, %d %b %Y %H:%M:%S +0000')
    # Setze das Datum der neuen Mail auf 10 Tage in der Vergangenheit
    new_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime('%a, %d %b %Y %H:%M:%S +0000')

    def fake_fetch(num, _):
        if num == b'1' or num == b'2':
            msg_bytes = f"Date: {old_date}\r\n\r\n".encode()
            return ('OK', [(b'1 (BODY[HEADER.FIELDS (DATE)] {44}', msg_bytes)])
        else:
            msg_bytes = f"Date: {new_date}\r\n\r\n".encode()
            return ('OK', [(b'3 (BODY[HEADER.FIELDS (DATE)] {44}', msg_bytes)])

    instance.fetch.side_effect = fake_fetch
    instance.store.return_value = ('OK', [])
    instance.expunge.return_value = ('OK', [])
    instance.logout.return_value = ('OK', [])
    # Run cleanup
    cli.cleanup()
    # Check that store was called for old mails only
    assert instance.store.call_count == 2
    # Check summary output
    assert mock_console.print.call_count > 0


@mock.patch('imap_cleanup.cli.console')
def test_cleanup_no_config_file(mock_console, tmp_path, monkeypatch):
    config_path = tmp_path / 'notfound.toml'
    monkeypatch.setattr(cli, 'CONFIG_FILE', str(config_path))
    cli.cleanup()
    mock_console.print.assert_called_with(mock.ANY)


@mock.patch('imap_cleanup.cli.console')
@mock.patch('imap_cleanup.cli.imaplib.IMAP4_SSL')
def test_cleanup_login_error(mock_imap, mock_console, fake_config, monkeypatch):
    monkeypatch.setattr(cli, 'CONFIG_FILE', str(fake_config))
    instance = mock_imap.return_value
    instance.login.side_effect = Exception('fail')
    cli.cleanup()
    assert mock_console.print.call_count > 0


@mock.patch('imap_cleanup.cli.console')
@mock.patch('imap_cleanup.cli.imaplib.IMAP4_SSL')
def test_cleanup_folder_search_error(mock_imap, mock_console, fake_config, monkeypatch):
    monkeypatch.setattr(cli, 'CONFIG_FILE', str(fake_config))
    instance = mock_imap.return_value
    instance.login.return_value = ('OK', [b'Logged in'])
    instance.select.return_value = ('OK', [b''])
    instance.search.return_value = ('NO', [b''])
    cli.cleanup()
    assert mock_console.print.call_count > 0
