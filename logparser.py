# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import time
import sqlite3
import tempfile
import paramiko
import argparse
from openpyxl import Workbook


def regexp(expr, item):
    return re.search(expr, item) is not None


def write_text_file(filename, rows):
    f = open(filename, mode="w", encoding="utf-8")
    for row in rows:
        if type(row[0]) == int:
            row = row[1:]
        row = list(map(lambda cell: str(cell), row))
        f.write(" ".join(row) + "\n")


def write_xlsx_file(filename, rows):
    wb = Workbook(write_only=True)
    ws = wb.create_sheet()
    for row in rows:
        if type(row[0]) == int:
            row = row[1:]
        ws.append(["%s" % str(cell) for cell in row])
    wb.save(filename)


def main():
    parser = argparse.ArgumentParser(description="LogParser is a flexible, cross-platform tool that provides "
                                                 "universal query access to text-based data such as log files",
                                     epilog="Created by Roman Merkushin", prog="logparser")
    parser.add_argument("-d", "--delete", action="store_true", help="delete temporary db file")
    parser.add_argument("-r", "--remote", action="store", type=str,
                        help="sftp connection string (username/password@host:port)")
    parser.add_argument("-f", "--format", action="store", type=str, help="log file format (see templates.json)")
    parser.add_argument("-e", "--encoding", action="store", type=str, default="utf-8",
                        help="log file encoding (default - UTF-8)")
    parser.add_argument("-i", "--input", action="store", type=str, help="path to log file")
    parser.add_argument("-q", "--query", action="store", type=str, help="select query")
    parser.add_argument("-o", "--output", action="store", type=str,
                        help="output filename (supported formats: txt, xlsx)")
    args = parser.parse_args()

    start_time = time.time()

    if args.format and args.input and args.query and args.output:
        base_dir = os.path.dirname(sys.argv[0])
        tmp_file = ""
        if args.remote:
            filename = os.path.basename(args.input)
            tmp_file = os.path.join(tempfile.gettempdir(), filename)
            db_filename = tmp_file + ".db"
        else:
            db_filename = args.input + ".db"
        db_exists = os.path.exists(db_filename)
        if db_exists and args.delete:
            os.remove(db_filename)
        connection = sqlite3.connect(db_filename)
        connection.create_function("REGEXP", 2, regexp)
        cursor = connection.cursor()

        if not db_exists or (db_exists and args.delete):
            with open(os.path.join(base_dir, "templates.json"), mode="r", encoding="utf-8") as data_file:
                log_format = json.load(data_file)[args.format]
            pattern = re.compile(log_format["pattern"])
            fields = log_format["fields"]
            payload_flag = log_format["payload"]

            table_query = "CREATE TABLE LOG (ID INTEGER PRIMARY KEY AUTOINCREMENT, %s TEXT, PAYLOAD TEXT)" \
                          % " TEXT, ".join(fields)
            cursor.execute(table_query)

            if args.remote:
                conn_pattern = r"(.*)\/(.*)@(.*):(.*)"
                conn_params = re.match(conn_pattern, args.remote)
                username = conn_params.group(1)
                password = conn_params.group(2)
                host = conn_params.group(3)
                port = int(conn_params.group(4))
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(host, port, username, password)
                sftp = client.open_sftp()
                sftp.get(args.input, tmp_file)
                log = open(tmp_file, mode="r", encoding=args.encoding)
            else:
                log = open(args.input, mode="r", encoding=args.encoding)

            payload = ""
            for line in log:
                string = " ".join(line.split())
                string = string.rstrip().replace("'", '"')
                parsed = pattern.match(string)
                if parsed:
                    if payload_flag and payload and cursor.lastrowid:
                        update_query = "UPDATE LOG set PAYLOAD = '%s' where ID = %s" \
                                       % (payload.rstrip(), cursor.lastrowid)
                        cursor.execute(update_query)
                        payload = ""
                    insert_query = "INSERT INTO LOG (%s) VALUES ('%s')" \
                                   % (", ".join(fields), "', '".join(parsed.groups()))
                    cursor.execute(insert_query)
                elif cursor.lastrowid:
                    payload += string + "\n"

            connection.commit()

        results = cursor.execute(args.query)
        output_format = os.path.splitext(args.output)[1].lower()
        if results:
            if output_format == ".txt":
                write_text_file(args.output, results)
            elif output_format == ".xlsx":
                write_xlsx_file(args.output, results)
            else:
                write_text_file(args.output, results)

        connection.close()
        print('Done! Time taken: %s' % (time.time() - start_time))

    else:
        parser.print_usage()

if __name__ == "__main__":
    main()