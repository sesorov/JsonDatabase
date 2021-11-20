import argparse
import sys
import enum
import pathlib

from pathlib import Path

from database import JsonDatabase
from table import Table, Document, JsonManager
from query import Query, where


class ReturnCode(enum.Enum):
    SUCCESS = 0
    CRITICAL = 1


class Modes(enum.Enum):
    GET = 'get'
    SET = 'set'


def main():
    """
    Main cmd interface for db
    :return:
    """

    return_code = ReturnCode.SUCCESS
    script = Path(__file__)

    parser = argparse.ArgumentParser(prog=script.name)

    subparsers = parser.add_subparsers(dest='mode')
    parser_get = subparsers.add_parser('get', help='Read DB')
    parser_set = subparsers.add_parser('set', help='Update/create DB')

    parser.add_argument('--path', required=True, help='Path to DB main .json')

    parser_get.add_argument('--tables_names', required=False, action='store_true', help='Get all tables names')
    parser_get.add_argument('--table', required=False, help='Table name')
    parser_get.add_argument('--all', required=False, action='store_true', help='Get all table elements')
    parser_get.add_argument('--search', required=False, nargs='+',
                            help="Aggregation [ sample: (where('name') == 'John') & (where('score') < 18) ]")

    parser_set.add_argument('--table', required=False, help='Table name')
    parser_set.add_argument('--create', required=False, action='store_true', help='Create option')
    parser_set.add_argument('--primary', required=False, nargs='+', default=[],
                            help='Primary keys list for table (default: [])')
    parser_set.add_argument('--add', required=False, nargs='+',
                            help='column_name:value:type column_name:value:type (--table required)'
                                 'Split multiple data by space, e.g.:'
                                 'name:John:string surname:Snow:string score:16:int')
    parser_set.add_argument('--key', required=False,
                            help='Add primary key (--table required)')
    parser_set.add_argument('--drop', required=False, help='database <path>/<name> OR table <name>')
    parser_set.add_argument('--delete', required=False, nargs='+',
                            help="Aggregation [ sample: (where('name') == 'John') & (where('score') < 18) ]")

    args = parser.parse_args()

    file_manager = JsonManager(Path(args.path))
    db = JsonDatabase(file_manager)

    if args.mode == Modes.GET.value:
        if args.tables_names:
            return db.get_tables_names()
        if args.all:
            if not args.table:
                raise ValueError('Please, provide --table')
            return db.table(args.table).get_all()
        if args.search:
            if not args.table:
                raise ValueError('Please, provide --table')
            return db.table(args.table).search(eval(' '.join(args.search)))  # TODO: SECURITY ALARM!

    elif args.mode == Modes.SET.value:
        if args.create:
            if args.table:
                _table = db.table(args.table, args.primary)
                return _table.name
            else:
                raise SyntaxError('Syntax: table <name>')
        if args.add:
            if args.table:
                record = {}
                for data in args.add:
                    raw = data.split(':')  # 0 - column, 1 - value, 2 - type
                    record[raw[0]] = eval(f"{raw[2]}('{raw[1]}')")  # TODO: SECURITY ALARM!
                db.table(args.table).add(record)
            else:
                raise SyntaxError('Syntax: table <name>')
        if args.key:
            if args.table:
                table = db.table(args.table)
                params = db.table("__params__")

                table.add_key(args.key)
                params.update(Document({"keys": [args.key]}, args.table), append=True)
            else:
                raise SyntaxError('Syntax: table <name>')
        if args.drop:
            raw = args.drop.split(' ')
            if raw[0] == 'database':
                db.drop(raw[1])
            elif raw[0] == 'table':
                db.drop_table(raw[1])
        if args.delete:
            if args.table:
                db.table(args.table).delete(eval(' '.join(args.delete)))    # TODO: SECURITY ALARM!
            else:
                raise ValueError('Please, provide --table')


if __name__ == '__main__':
    print(main())
