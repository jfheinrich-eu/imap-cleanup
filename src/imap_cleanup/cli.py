import os
import toml
import getpass
import imaplib
import email
import questionary
from rich.console import Console
from rich.table import Table
from tqdm import tqdm
from datetime import datetime, timedelta, timezone

CONFIG_FILE = 'config.toml'
console = Console()

def cleanup():
    if not os.path.exists(CONFIG_FILE):
        console.print(f'[red]Config file {CONFIG_FILE} not found. Please run init first.[/red]')
        return
    with open(CONFIG_FILE, 'r') as f:
        config = toml.load(f)
    summary = []
    for accounts in config.get('accounts', []):       
        server = accounts.get('server')
        port = accounts.get('port')
        user = accounts.get('user')
        password = accounts.get('password')
        ssl = accounts.get('ssl')
        folders = accounts.get('folders')
        console.print(f'\n[bold]Account:[/bold] {user}@{server}:{port} (SSL: {ssl})')
        try:
            if ssl:
                M = imaplib.IMAP4_SSL(server, port)
            else:
                M = imaplib.IMAP4(server, port)
            M.login(user, password)
        except Exception as e:
            console.print(f'[red]Login failed: {e}[/red]')
            continue
        for folder, opts in folders.items():
            purge = opts.get('purge', False)
            retention = opts.get('retention_days', 30)
            if not purge or not isinstance(retention, int) or retention <= 0:
                continue
            try:
                M.select(f'"{folder}"')
                typ, data = M.search(None, 'ALL')
                if typ != 'OK':
                    console.print(f'[yellow]Could not search folder {folder}[/yellow]')
                    continue
                msg_nums = data[0].split()
                deleted = 0
                cutoff = datetime.now(timezone.utc) - timedelta(days=int(retention))
                with tqdm(total=len(msg_nums), desc=f"{user}:{folder}", unit="mail") as pbar:
                    for num in msg_nums:
                        typ, msg_data = M.fetch(num, '(BODY.PEEK[HEADER.FIELDS (DATE)])')
                        if typ != 'OK':
                            pbar.update(1)
                            continue
                        msg_date = None
                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                date_str = msg.get('Date')
                                try:
                                    msg_date = email.utils.parsedate_to_datetime(date_str)
                                except Exception:
                                    pass
                        if msg_date and msg_date < cutoff:
                            M.store(num, '+FLAGS', '\\Deleted')
                            deleted += 1
                        pbar.update(1)
                M.expunge()
                summary.append((user, folder, deleted))
            except Exception as e:
                console.print(f'[red]Error in folder {folder}: {e}[/red]')
        M.logout()
    # Summary
    table = Table(title="Cleanup Summary")
    table.add_column("Account")
    table.add_column("Folder")
    table.add_column("Deleted Mails", justify="right")
    for user, folder, deleted in summary:
        table.add_row(user, folder, str(deleted))
    console.print(table)

def get_imap_folders(server, port, user, password, ssl, imap_class_ssl=imaplib.IMAP4_SSL, imap_class=imaplib.IMAP4):
    if ssl:
        M = imap_class_ssl(server, port)
    else:
        M = imap_class(server, port)
    M.login(user, password)
    typ, data = M.list()
    if typ != 'OK':
        raise Exception('Could not list folders')
    folders = []
    for line in data:
        parts = line.decode().split(' "/" ')
        if len(parts) == 2:
            folders.append(parts[1].strip('"'))
    M.logout()
    return folders

def init_config(
    config_file=CONFIG_FILE,
    input_func=questionary.text,
    select_func=questionary.select,
    checkbox_func=questionary.checkbox,
    getpass_func=getpass.getpass,
    get_folders_func=get_imap_folders,
    console=console,
    toml_module=toml
):
    console.print('[bold]IMAP Account Configuration[/bold]')
    server = input_func('IMAP Server:').ask()
    port = int(input_func('Port (e.g. 993):', default='993').ask())
    user = input_func('Username:').ask()
    password = getpass_func('Password: ')
    ssl = select_func('Use SSL?', choices=['Yes', 'No']).ask() == 'Yes'
    try:
        folders = get_folders_func(server, port, user, password, ssl)
    except Exception as e:
        console.print(f'[red]Error fetching folders: {e}[/red]')
        return
    selected_folders = checkbox_func('Which folders to monitor?', choices=folders).ask()
    folder_config = {folder: {'purge': False, 'retention_days': 30} for folder in selected_folders}
    config = {
        'accounts': [
            {
                server: {
                    'server': server,
                    'port': port,
                    'user': user,
                    'password': password,
                    'ssl': ssl,
                    'folders': folder_config
                }
            }
        ]
    }
    with open(config_file, 'w') as f:
        toml_module.dump(config, f)
    console.print(f'[green]Configuration saved to {config_file}[/green]')

def main():
    import argparse
    parser = argparse.ArgumentParser(description='IMAP Cleanup Tool')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    parser_init = subparsers.add_parser('init', help='Initialize configuration')
    parser_cleanup = subparsers.add_parser('cleanup', help='Cleanup emails according to config')

    args = parser.parse_args()
    if args.command == 'init':
        init_config()
    elif args.command == 'cleanup':
        cleanup()