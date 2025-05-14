import redis
import sys
import os
from datetime import datetime
import moment

class Params:
    def __init__(self, defaults):
        self.opts = defaults
        self.opt_count = len(sys.argv) - 1

    def getOpts(self):
        i = 1
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg.startswith("--"):
                key = arg[2:].replace("-", "_")
                if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
                    value = sys.argv[i + 1]
                    if value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    self.opts[key] = value
                    i += 2
                else:
                    self.opts[key] = True
                    i += 1
            else:
                if "---" not in self.opts:
                    self.opts["---"] = []
                self.opts["---"].append(arg)
                i += 1
        return self.opts

    def getOptCount(self):
        return self.opt_count

    def showUsage(self):
        print("python " + os.path.basename(__file__) + " [options] inputs", file=sys.stderr)
        print("", file=sys.stderr)
        print("available options:", file=sys.stderr)
        print("                 ", file=sys.stderr)
        print("                 --data-format YYYYMMDD", file=sys.stderr)
        print("                 ", file=sys.stderr)
        print("                 --symbol-index 0", file=sys.stderr)
        print("                 --date-index   1", file=sys.stderr)
        print("                 --open-index   2", file=sys.stderr)
        print("                 --high-index   3", file=sys.stderr)
        print("                 --low-index    4", file=sys.stderr)
        print("                 --close-index  5", file=sys.stderr)
        print("                 --volume-index 6", file=sys.stderr)
        print("                 ", file=sys.stderr)
        print("                 --host       localhost", file=sys.stderr)
        print("                 --port         6379", file=sys.stderr)
        print("                 --database     0", file=sys.stderr)
        print("                 ", file=sys.stderr)
        print("                 --key-prefix   a-key-prefix", file=sys.stderr)

params = Params({
    "database": 0,
    "host": "localhost",
    "port": 6379,
    "convert_date": True,
    "date_format": 'YYYYMMDD',
    "dry_run": True,
    "key_prefix": "",
    "symbol_index": -1, # 0,
    "date_index": -1, # 1,
    "open_index": -1, # 2,
    "high_index": -1, # 3,
    "low_index": -1, # 4,
    "close_index": -1, # 5,
    "volume_index": -1, # 6,
})

opts = params.getOpts()
opt_count = params.getOptCount()

if opt_count < 1:
    params.showUsage()
    sys.exit(-1)

symbol_index = opts.get("symbol_index", 0)
date_index = opts.get("date_index", 1)
open_index = opts.get("open_index", 2)
high_index = opts.get("high_index", 3)
low_index = opts.get("low_index", 4)
close_index = opts.get("close_index", 5)
volume_index = opts.get("volume_index", 6)

key_prefix = opts.get("key_prefix", "")
date_format = opts["date_format"]
convert_date = opts["convert_date"]

inputs = opts.get("---", [])
if not isinstance(inputs, list):
    inputs = [inputs]

print(f"Importing data from {inputs} to redis server {opts['host']}:{opts['port']} database {opts['database']}")

client = redis.Redis(host=opts["host"], port=opts["port"], db=opts["database"])

def format_date(d):
    month = str(d.month).zfill(2)
    day = str(d.day).zfill(2)
    year = str(d.year)
    return year + month + day

def to_date(date_str):
    return moment.date(date_str, date_format).to_date()

def import_file(input_file):
    tested = False
    see_header = False
    try:
        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    print("Empty line")
                    continue

                # convert to lowercase
                if not see_header:
                    lowcase_line = line.lower()
                    # check if the line contains words: date, open, high, low, close, volume
                    if "date" in lowcase_line or "open" in lowcase_line or "high" in lowcase_line or "low" in lowcase_line or "close" in lowcase_line or "volume" in lowcase_line:
                        see_header = True
                        print("Header line")
                        continue

                print(line)
                tokens = line.split(",")

                date_str = tokens[date_index]
                convert_date = True

                # if the length of the date string is 8, we assume it's in YYYYMMDD format
                if len(date_str) == 8:
                    convert_date = False

                if convert_date:
                    try:
                        # Format as DD/MM/YYYY
                        d = datetime.strptime(date_str, "%d/%m/%Y")
                    except ValueError:
                        try:
                            d = datetime.strptime(date_str, "%Y-%m-%d")  # Assuming ISO format as fallback
                        except ValueError:
                            print(f"Unrecognized date format: {date_str}", file=sys.stderr)
                            print(f"In line: {line}", file=sys.stderr)
                            print("Please consider converting the date into a simple ISO standard format first, such as DD/MM/YYYY", file=sys.stderr)
                            sys.exit(1)
                    # convert to YYYYMMDD
                    date_str = format_date(d)

                data_str = f'{{"O": {float(tokens[open_index])}, "H": {float(tokens[high_index])}, "L": {float(tokens[low_index])}, "C": {float(tokens[close_index])}, "V": {int(tokens[volume_index])}}}'

                key_str = key_prefix + tokens[symbol_index]
                client.hmset(key_str, {date_str: data_str})
                print(f"{key_str} inserted")

                if not tested:
                    value = client.hget(key_str, date_str)
                    if not value:
                        print(f"Can't find the value for key: {key_str}, field: {date_str}", file=sys.stderr)
                        sys.exit(-1)
                    tested = True
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)

config = client.hgetall("tyosis-config")
if not config:
    config = {}
else:
    config = {k.decode('utf-8'): v.decode('utf-8') for k, v in config.items()}

if not key_prefix or len(key_prefix) == 0:
    key_prefix = config.get("key_prefix", "")

if (not symbol_index or symbol_index < 0): 
    symbol_index = int(config.get("symbol_index", 0))
if (not date_index or date_index < 0):
    date_index = int(config.get("date_index", 1))
if (not open_index or open_index < 0):
    open_index = int(config.get("open_index", 2))
if (not high_index or high_index < 0):
    high_index = int(config.get("high_index", 3))
if (not low_index or low_index < 0):
    low_index = int(config.get("low_index", 4))
if (not close_index or close_index < 0):
    close_index = int(config.get("close_index", 5))
if (not volume_index or volume_index < 0):
    volume_index = int(config.get("volume_index", 6))

client.hmset("tyosis-config", {
    "key-prefix": key_prefix,
    "symbol-index": symbol_index,
    "date-index": date_index,
    "open-index": open_index,
    "high-index": high_index,
    "low-index": low_index,
    "close-index": close_index,
    "volume-index": volume_index,
})

for input_file in inputs:
    import_file(input_file)

sys.exit(0)