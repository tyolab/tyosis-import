/*
 *   Copyright (c) 2020 TYONLINE TECHNOLOGY PTY. LTD. (TYO Lab)
 *   All rights reserved.
 *
 *   @author Eric Tang (eric@tyo.com.au)
 *   @twitter @_e_tang
 */

const redis = require("redis");

const readline = require('readline');
const fs = require('fs');
const moment = require('moment');

var Params = require('node-programmer/params');

// Exit codes -- a caller (scripts/import_stocks.sh, cron) must be able to tell
// "nothing landed" from success:
//   0  every data row of every input was written to Redis
//   1  at least one row failed to write, or an input could not be read
//   2  could not talk to Redis at all (connection refused / lost), or bad usage
const EXIT_OK = 0;
const EXIT_WRITE_FAILED = 1;
const EXIT_CONNECTION = 2;

var params = new Params({
    database: 0,
    host: "localhost",
    port: 6379,
    "convert-date": true,
    "date-format": 'YYYYMMDD', // @todo "dd MMM yyyy"
    "dry-run": true,
    "key-prefix": "",
    "symbol-index": 0,
    "date-index": 1,
    "open-index": 2,
    "high-index": 3,
    "low-index": 4,
    "close-index": 5,
    "volume-index": 6,
});

var currentDate = new Date();
var currentMonth = currentDate.getMonth();

var opts = params.getOpts();
var optCount = params.getOptCount();

params.showUsage = function() {
    console.error("node " + __filename + " [options] inputs");
    console.error('');
    console.error('available options:');
    console.error('                 ');
    console.error('                 --convert-date true');
    console.error('                 --data-format YYYYMMDD');
    console.error('                 ');
    console.error('                 --symbol-index 0');
    console.error('                 --date-index   1');
    console.error('                 --open-index   2');
    console.error('                 --high-index   3');
    console.error('                 --low-index    4');
    console.error('                 --close-index  5');
    console.error('                 --volume-index 6');
    console.error('                 ');
    console.error('                 --host         localhost');
    console.error('                 --port         6379');
    console.error('                 --database     0');
    console.error('                 ');
    console.error('                 --key-prefix   a-key-prefix');
}

if (optCount < 1) {
    params.showUsage();
    process.exit(EXIT_CONNECTION);
}

var symbolIndex = opts["symbol-index"] || 0,
    dateIndex = opts["date-index"] || 1,
    openIndex = opts["open-index"] || 2,
    highIndex = opts["high-index"] || 3,
    lowIndex = opts["low-index"] || 4,
    closeIndex = opts["close-index"] || 5,
    volumeIndex = opts["volume-index"] || 6;

var keyPrefix = opts["key-prefix"] || "";
var dateFormat = opts["date-format"];
var convertDate = opts["convert-date"];

var inputs = opts['---'];
if (!Array.isArray(inputs))
    inputs = [inputs];
inputs = inputs.filter((input) => typeof input === 'string' && input.length > 0);

if (inputs.length === 0) {
    console.error("No input file given.");
    params.showUsage();
    process.exit(EXIT_CONNECTION);
}

console.log("Importing data from " + inputs + " to redis" + " server " + opts.host + ":" + opts.port + " database " + opts.database + "");

// The redis v3 client retries forever by default and, with no 'error'
// listener, a connection failure was an uncaught exception at best -- or, for
// a Redis that stayed down, the offline queue just swallowed every write and
// the process still exited 0 once the input file had been read. Bound the
// retries and turn any connection error into a hard, non-zero exit.
const client = redis.createClient({
    host: opts.host,
    port: opts.port - 0,
    enable_offline_queue: false,
    retry_strategy: function (options) {
        if (options.attempt > 3) {
            return new Error("Could not connect to redis at " + opts.host + ":" + opts.port + " after " + (options.attempt - 1) + " attempts (" + (options.error && options.error.code) + ")");
        }
        return Math.min(options.attempt * 200, 1000);
    },
});

client.on('error', function (err) {
    console.error("Redis error: " + (err && err.message || err));
    process.exit(EXIT_CONNECTION);
});

function formatDate(d) {
    var
        month = '' + (d.getMonth() + 1),
        day = '' + d.getDate(),
        year = '' + d.getFullYear();

    if (month.length < 2)
        month = '0' + month;
    if (day.length < 2)
        day = '0' + day;

    return [year, month, day].join('');
}

function toDate(dateStr) {
    return moment(dateStr, dateFormat).toDate();
}

// Rejects on error (the old helper logged and swallowed it, so a failed write
// looked identical to a successful one).
function promisify () {
    var args = Array.from(arguments);
    var func = args.shift();

    return new Promise((resolve, reject) => {
        args.push(function (err, value) {
            if (err) return reject(err);
            resolve(value);
        });
        func.apply(client, args);
    });
}

function HMSET () {
    return promisify.apply(null, [client.HMSET].concat(Array.from(arguments)));
}

function HGET (key, field) {
    return promisify(client.HGET, key, field);
}

function SELECT (db) {
    return promisify(client.SELECT, db);
}

function HGETALL (key) {
    return promisify(client.HGETALL, key);
}

// A day-file's first line is a header ("Code,Date,Open,...") and stray lines
// (blank, comment, ragged) occasionally show up; these used to be written as
// data -- every market carries a "<prefix>Code" hash with a "Date" field.
function parseRow(line) {
    var tokens = line.split(",");
    if (tokens.length <= volumeIndex)
        return { skip: "too few columns" };

    var symbol = tokens[symbolIndex] && tokens[symbolIndex].trim();
    var dateStr = tokens[dateIndex] && tokens[dateIndex].trim();
    if (!symbol || !dateStr)
        return { skip: "missing symbol/date" };

    var open = parseFloat(tokens[openIndex]),
        high = parseFloat(tokens[highIndex]),
        low = parseFloat(tokens[lowIndex]),
        close = parseFloat(tokens[closeIndex]),
        volume = parseInt(tokens[volumeIndex]);
    if (isNaN(open) || isNaN(high) || isNaN(low) || isNaN(close))
        return { skip: "non-numeric OHLC (header?)" };
    if (isNaN(volume))
        volume = 0;

    if (convertDate) {
        // parse date in a format when only a date format is provided
        // it can be later parse in the backtest tool or others
        // and we store date in format 'YYYYMMDD' as key for the later easy retrieval of data
        var d = new Date(dateStr);
        if (d == 'Invalid Date')
            return { error: 'Unrecognized date format: ' + dateStr + ' (consider converting the date into a simple ISO standard format first, such as YYYY-MM-DD)' };
        dateStr = moment(d).format(dateFormat);
    }
    else if (!/^\d{8}$/.test(dateStr)) {
        return { skip: "date is not YYYYMMDD" };
    }

    return {
        key: keyPrefix + symbol,
        field: dateStr,
        value: `{"O": ${open}, "H": ${high}, "L": ${low}, "C": ${close}, "V": ${volume}}`,
    };
}

// Resolves to { inserted, skipped, failed } once EVERY write for the file has
// been acknowledged by Redis. The old version exited the process the moment
// readline hit EOF, with the writes still in flight.
function importFile(input) {
    return new Promise((resolve) => {
        var stats = { input, inserted: 0, skipped: 0, failed: 0 };
        var pending = [];
        var verified = false;

        var done = false;
        var finish = function () {
            if (done) return;
            done = true;
            Promise.all(pending).then(function () { resolve(stats); });
        };

        const readInterface = readline.createInterface({
            input: fs.createReadStream(input),
            console: false
        });

        // readline re-emits the stream's error on the interface; unhandled, an
        // unreadable input (ENOENT, EACCES) crashed the whole run
        readInterface.on('error', function (err) {
            console.error("Cannot read " + input + ": " + err.message);
            stats.failed++;
            finish();
        });

        readInterface.on('line', function(line) {
            if (!line || line.trim().length == 0) {
                stats.skipped++;
                return;
            }

            console.log(line);
            var row = parseRow(line);
            if (row.skip) {
                console.log("Skipped (" + row.skip + "): " + line);
                stats.skipped++;
                return;
            }
            if (row.error) {
                console.error(row.error);
                console.error('In line: ' + line);
                stats.failed++;
                return;
            }

            var write = HMSET(row.key, row.field, row.value)
                .then(function () {
                    console.log(row.key + " inserted");
                    stats.inserted++;
                    // read back the first row of each file to catch a Redis that
                    // acknowledges but does not actually persist (wrong database, ACL...)
                    if (!verified) {
                        verified = true;
                        return HGET(row.key, row.field).then(function (value) {
                            if (!value) {
                                console.error("Can't find the value for key: " + row.key + ", field: " + row.field + " after writing it");
                                stats.failed++;
                            }
                        });
                    }
                })
                .catch(function (err) {
                    console.error("Failed to write " + row.key + " " + row.field + ": " + (err && err.message || err));
                    stats.failed++;
                });
            pending.push(write);
        });

        readInterface.on('close', finish);
    });
}

async function main() {
    await SELECT(opts.database);

    var config = (await HGETALL("tyosis-config")) || {};

    // remember last time setting unless getting overriden from the command line
    if (!opts["key-prefix"] || !opts["key-prefix"].length)
        keyPrefix = config["key-prefix"] || "";
    else
        keyPrefix = opts["key-prefix"];

    if (config["symbol-index"])
        symbolIndex = config["symbol-index"];

    if (config["date-index"])
        dateIndex = config["date-index"];

    if (config["open-index"])
        openIndex = config["open-index"];

    if (config["high-index"])
        highIndex = config["high-index"];

    if (config["low-index"])
        lowIndex = config["low-index"];

    if (config["close-index"])
        closeIndex = config["close-index"];

    if (config["volume-index"])
        volumeIndex = config["volume-index"];

    await HMSET("tyosis-config",
        "key-prefix", keyPrefix,
        "symbol-index", symbolIndex,
        "date-index", dateIndex,
        "open-index", openIndex,
        "high-index", highIndex,
        "low-index", lowIndex,
        "close-index", closeIndex,
        "volume-index", volumeIndex,
    );

    var totals = { inserted: 0, skipped: 0, failed: 0 };
    for (const input of inputs) {
        var stats = await importFile(input);
        console.log(input + ": " + stats.inserted + " inserted, " + stats.skipped + " skipped, " + stats.failed + " failed");
        totals.inserted += stats.inserted;
        totals.skipped += stats.skipped;
        totals.failed += stats.failed;
    }

    console.log("Done: " + totals.inserted + " inserted, " + totals.skipped + " skipped, " + totals.failed + " failed" + (inputs.length > 1 ? " across " + inputs.length + " files" : ""));
    return totals.failed > 0 ? EXIT_WRITE_FAILED : EXIT_OK;
}

// With the offline queue off, nothing may be sent before the connection is up.
client.once('ready', function () {
    main()
        .then(function (code) {
            client.quit(function () { process.exit(code); });
        })
        .catch(function (err) {
            console.error(err && err.message || err);
            process.exit(EXIT_CONNECTION);
        });
});
