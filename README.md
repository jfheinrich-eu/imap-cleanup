<p align="center">
  <img src="assets/logo.svg" alt="imap-cleanup logo" width="200"/>
</p>

# imap-cleanup

A Python tool for automated cleanup of IMAP mailboxes based on configurable rules.

## Features
- Interactive initialization of IMAP configuration
- Selection and management of multiple IMAP accounts and folders
- Configuration in TOML format
- (Planned) Automatic deletion of old emails based on retention period

## Project Structure

```
imap-cleanup/
├── src/
│   └── imap_cleanup/
│       ├── __init__.py
│       └── cli.py
├── tests/
│   └── test_cli.py
├── imap_cleanup.py
├── requirements.txt
├── pyproject.toml
├── LICENSE
└── README.md
```

## Installation (Development)

```bash
pip install -r requirements.txt
```

## Usage

```bash
python imap_cleanup.py init
```

## Run Tests

```bash
pytest
```

## Packaging
The project is ready for modern packaging with `pyproject.toml`.

## Beispiel config.toml

```toml
[[accounts]]
server = "imap.example.com"
port = 993
user = "user@example.com"
password = "dein_passwort"
ssl = true

[accounts.folders]
INBOX = { retention_days = 30 }
Archive = { retention_days = 90 }
```

**Achtung:** Das Passwort wird im Klartext in der Konfigurationsdatei gespeichert. Dies stellt ein Sicherheitsrisiko dar. Stelle sicher, dass die Datei geschützt ist und erwäge alternative Methoden zur sicheren Passwortspeicherung (z.B. Umgebungsvariablen oder Keyring).
