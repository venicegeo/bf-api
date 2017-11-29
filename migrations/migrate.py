import json, os, shlex, subprocess, sys

from argparse import ArgumentParser, FileType, Namespace
from getpass import getpass
from os import path

QUIET = False
VERBOSE = False

def log(*messages, error=False, detail=False):
    if error:
        print("[ERROR]", *messages, file=sys.stderr)
    elif QUIET:
        pass
    elif detail:
        if VERBOSE:
            print(*messages)
    else:
        print(*messages)

def parse_args() -> Namespace:
    parser = ArgumentParser(
        prog='migrate.py', description='Run bf-api\'s migration scripts',
        epilog='Non-interactively, this will run and apply all appropriate '
               'migrations to the database described by your environment variables')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument('-i', '--interactive', action='store_true')
    parser.add_argument('--changelog', type=str, default=None)
    parser.add_argument('--liquibase', type=str, default=None,
                        help='Path to liquibase runnable JAR')
    parser.add_argument('--classpath', type=str, default=None,
                        help='Java classpath to pass to Liquibase')
    parser.add_argument('--dry-run', action='store_true', dest='dry',
                        help='dry run (print output, do not apply changes)')
    parser.add_argument('lb_args', metavar='LIQUIBASE_ARGS', type=str, nargs='+',
                        help='command args to pass through to Liquibase')
    return parser.parse_args()

def configure_environment() -> dict:
    log("Reading configuration from environment...", detail=True)
    vcap_json = os.environ.get('VCAP_SERVICES')
    if not vcap_json:
        log("VCAP_SERVICES environment variable missing", error=True)
        raise ValueError("VCAP_SERVICES environment variable missing")
    vcap = json.loads(vcap_json)

    output = {
        'hostname': '',
        'username': '',
        'password': '',
        'database': '',
        'port': 0,
    }

    for config in vcap.get('user-provided', []):
        if config.get('name') != 'pz-postgres':
            continue
        creds = config.get('credentials', {})
        output.update(creds)
        break
    else:
        log("pz-postgres configuration in environment not found", error=True)
    return output


def configure_interactive():
    log("Please input your database details:")
    return {
        'hostname': input("Hostname (default: localhost): ") or 'localhost',
        'port': input("Port (default: 5432): ") or '5432',
        'database': input("Database name (default: beachfront): ") or 'beachfront',
        'username': input("Username: "),
        'password': getpass("Password: ")
    }

def get_migrations_dir():
    return os.path.dirname(os.path.abspath(__file__))

def get_liquibase_location(path):
    path = path or os.path.join(get_migrations_dir(), './liquibase.jar')
    return os.path.normpath(path)

def get_changelog_location(path):
    path = path or os.path.join(get_migrations_dir(), './changelog.xml')
    return os.path.normpath(path)

def get_postgresql_jar(path):
    path = path or os.path.join(get_migrations_dir(), './postgresql.jar')
    return os.path.normpath(path)

def run_liquibase(liquibase_path, changelog_path, classpath, config, lb_args=[], dry=False):
    log("Using changelog at:", changelog_path)
    if not os.path.exists(changelog_path):
        log("Changelog missing! Create it or specify it using --changelog", error=True)
        sys.exit(1)
    log("Using Liquibase at:", liquibase_path)
    if not os.path.exists(liquibase_path):
        log("Liquibase executable missing! Put it at the expected location or "
            "specify it using --liquibase", error=True)
        sys.exit(1)
    log("Using classpath:", classpath)

    if not lb_args:
        log("No Liquibase args specified; it will likely complain about this", error=True)

    cmd = ['java',
        '-jar', liquibase_path,
        '--changeLogFile=' + changelog_path,
        '--username=' + config['username'],
        '--password=' + config['password'],
        '--url=jdbc:postgresql://{hostname}:{port}/{database}'.format(**config),
        '--driver=org.postgresql.Driver',
        '--classpath=' + classpath,
    ] + lb_args
    log('Command is:', ' '.join(cmd), detail=True)
    if not dry:
        log('Running...')
        retcode = subprocess.call(cmd)
        if retcode != 0:
            log('Non-zero return code!', retcode, error=True)
            sys.exit(retcode)
    else:
        log('Dry run, not doing anything.')

def main():
    global QUIET, VERBOSE
    args = parse_args()
    QUIET = args.quiet
    VERBOSE = args.verbose

    if args.interactive:
        config = configure_interactive()
    else:
        config = configure_environment()

    log("Got Postgres configuration:", json.dumps(config, indent=2), detail=True)

    changelog = get_changelog_location(args.changelog)
    liquibase = get_liquibase_location(args.liquibase)
    classpath = get_postgresql_jar(args.classpath)
    lb_args = args.lb_args
    run_liquibase(liquibase, changelog, classpath, config, lb_args, dry=args.dry)

    log('Done.')

if __name__ == '__main__': main()
