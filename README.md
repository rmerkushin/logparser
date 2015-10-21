LogParser
=========

LogParser is a flexible, cross-platform tool that provides universal query access to text-based data such as log files.

**Download binary**:
- :arrow_down: [Mac OS](https://github.com/rmerkushin/logparser/releases/download/v0.2/logparser-mac-0.2.zip)
- :arrow_down: [Windows](https://github.com/rmerkushin/logparser/releases/download/v0.2/logparser-win-0.2.zip)

### Input formats
- log4j log files

### Output formats
- Plain text
- Microsoft Excel (.xlsx)

### Features
- [SQLite SQL](http://www.sqlite.org/lang.html) full support
- Regular expressions in query
- Remote log parsing (sftp)
- Custom log format templates

### Usage example
Сommand line arguments:
- -d, --delete - delete temporary DB file (without this flag, the program will use previous processing results if they exist)
- -r, --remote - sftp connection string (username/password@host:port)
- -f, --format - log file format
- -e, --encoding - log file encoding (default - UTF-8)
- -i, --input - path to log file
- -q, --query - select query
- -o, --output - output filename (output format depends on extension)
```shell
logparser -f log4j -i /path/to/log/file -q "SELECT * FROM LOG WHERE LEVEL = 'ERROR" -o /path/to/output/file.txt
```
Example above shows how get all messages from log with logging level "ERROR".

### Сustom log format
You can add a new log format by editing templates.json file:
```json
{
    "format_name": {
        "pattern": "regular_expression",
        "payload": true,
        "fields": ["FIELD_1", "FIELD_2", "...", "FIELD_N"]
    }
}
```
`format_name` - log file format name (without spaces and special symbols).

`pattern` - regular expression pattern for line of log file. Separated elements should be grouped.

`payload` - flag. If true, all lines which do not match to pattern will be added to "PAYLOAD" field.

`fields` - table fields that will be filled values from parsed lines of log file. Fields should be correlated to regex pattern groups.

### Known issuses
- in case of log file contains special symbols the program might be crashed (see image below for details)
![](https://raw.githubusercontent.com/rmerkushin/logparser/master/special_symbols.png)