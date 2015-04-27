# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import sqlite3
import tempfile
import paramiko
import argparse
from openpyxl import Workbook


def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None


def write_text_file(file_name, rows):
    f = open(file_name, mode="w", encoding="utf-8")
    for row in rows:
        if type(row[0]) == int:
            row = row[1:]
        row = list(map(lambda x: str(x), row))
        row = " ".join(row)
        f.write(row + "\n")


def write_xlsx_file(file_name, rows):
    wb = Workbook()
    ws = wb.active
    i = 1
    for row in rows:
        if type(row[0]) == int:
            row = row[1:]
        row = list(map(lambda x: str(x), row))
        j = 1
        for cell in row:
            ws.cell(row=i, column=j).value = cell
            j += 1
        i += 1
    wb.save(file_name)


def main():
    parser = argparse.ArgumentParser(description="LogParser is a flexible, cross-platform tool that provides "
                                                 "universal query access to text-based data such as log files",
                                     epilog="Created by Roman Merkushin", prog="logparser")
    parser.add_argument("-r", "--remote", action="store", type=str,
                        help="sftp connection string (username/password@host:port)")
    parser.add_argument("-f", "--format", action="store", type=str, help="log file format (see templates.json)")
    parser.add_argument("-i", "--input", action="store", type=str, help="path to log file")
    parser.add_argument("-q", "--query", action="store", type=str, help="select query")
    parser.add_argument("-o", "--output", action="store", type=str,
                        help="output filename (supported formats: txt, xlsx)")
    options = parser.parse_args()
    options = vars(options)

    if options["format"] and options["input"] and options["query"] and options["output"]:
        base_dir = os.path.dirname(sys.argv[0])
        with open(os.path.join(base_dir, "templates.json"), mode="r", encoding="utf-8") as data_file:
            log_format = json.load(data_file)[options["format"]]
        pattern = log_format["pattern"]
        fields = log_format["fields"]
        payload_flag = log_format["payload"]
        if payload_flag:
            fields.append("PAYLOAD")
        table_query = "CREATE TABLE LOG (ID INTEGER PRIMARY KEY AUTOINCREMENT, {} TEXT)"
        table_query = table_query.format(" TEXT, ".join(fields))

        connection = sqlite3.connect(":memory:")
        connection.create_function("REGEXP", 2, regexp)
        cursor = connection.cursor()
        cursor.execute(table_query)

        if options["remote"]:
            tmp_file = os.path.join(tempfile.gettempdir(), "tmp.log")
            conn_pattern = r"(.*)\/(.*)@(.*):(.*)"
            conn_params = re.search(conn_pattern, options["remote"])
            username = conn_params.group(1)
            password = conn_params.group(2)
            host = conn_params.group(3)
            port = int(conn_params.group(4))
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, port, username, password)
            sftp = client.open_sftp()
            sftp.get(options["input"], tmp_file)
            log = open(tmp_file, mode="r", encoding="utf-8")
        else:
            log = open(options["input"], mode="r", encoding="utf-8")
        payload = ""
        if payload_flag:
            insert_fields = ", ".join(fields[:-1])
        else:
            insert_fields = ", ".join(fields)

        for line in log:
            string = " ".join(line.split())
            string = string.rstrip().replace("'", '"')
            parsed = re.search(pattern, string)
            if parsed:
                if payload_flag and payload and cursor.lastrowid > 0:
                    update_query = "UPDATE LOG set PAYLOAD = '{0}' where ID = {1}".format(payload, cursor.lastrowid)
                    cursor.execute(update_query)
                    payload = ""
                insert_query = "INSERT INTO LOG ({}) VALUES ('{}')".format(insert_fields, "', '".join(parsed.groups()))
                cursor.execute(insert_query)
            else:
                payload += string + "\n"

        connection.commit()

        results = cursor.execute(options["query"])
        output_format = os.path.splitext(options["output"])[1].lower()
        if results:
            if output_format == ".txt":
                write_text_file(options["output"], results)
            elif output_format == ".xlsx":
                write_xlsx_file(options["output"], results)
            else:
                write_text_file(options["output"], results)

        connection.close()
    else:
        parser.print_usage()

if __name__ == "__main__":
    main()