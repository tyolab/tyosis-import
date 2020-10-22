/*
 *   Copyright (c) 2020 TYONLINE TECHNOLOGY PTY. LTD. (TYO Lab)
 *   All rights reserved.
 * 
 *   @author Eric Tang (eric@tyo.com.au)
 *   @twitter @_e_tang
 */

const redis = require("redis");
const client = redis.createClient();

const readline = require('readline');
const fs = require('fs');
const moment = require('moment');

var Params = require('node-programmer/params');

var params = new Params({
    database: 0,
    host: "localhost",
    port: 6379,
    "date-format": null, // "dd MMM yyyy"
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

if (optCount < 1) {
    params.showUsage();
    process.exit(-1);
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

var inputs = opts['---'];
if (!Array.isArray(inputs))
    inputs = [inputs];

console.log("Importing data from " + inputs);

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

function importFile(input) {
    const readInterface = readline.createInterface({
        input: fs.createReadStream(input),
        output: process.stdout,
        console: false
    });

    readInterface.on('line', function(line) {
        console.log(line);
        var tokens = line.split(",");
        // #1 Symbol
        // #2 Date
        // #3 Open
        // #4 High
        // #5 Low
        // #6 Close
        // #7 Volume

        var dateStr = tokens[dateIndex];

        // the to date format
        if (dateFormat && dateFormat.length) {
            // we store date in a format when only a date format is provided
            // it can be later parse in the backtest tool or others
            // and i.e. we can store date in format 'YYYYMMDD'
            var d = new Date(dateStr); 
            dateStr = moment(d).format(dateFormat);
        }
        var dataStr = `{"O": ${tokens[openIndex]}, "H": ${tokens[highIndex]}, "L": ${tokens[lowIndex]}, "C": ${tokens[closeIndex]}, "V": ${tokens[volumeIndex]}}`;

        var keyStr = opts["key-prefix"] + tokens[symbolIndex]
        client.HMSET(keyStr, 
            dateStr, dataStr
            );

    });

    readInterface.on('close', function(line) {
        process.exit(0);
    });
}

client.select(opts.database, function() {
    
    client.hgetall("tyosis-config", function(err, config) {
        config = config || {};

        // remember last time setting unless getting overriden from the command line
        if (!opts["key-prefix"] || opts["key-prefix"].length)
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

        client.hmset("tyosis-config",
        "key-prefix", keyPrefix,
        "symbol-index", symbolIndex,
        "date-index", dateIndex,
        "open-index", openIndex,
        "high-index", highIndex,
        "low-index", lowIndex,
        "close-index", closeIndex,
        "volume-index", volumeIndex,
        );

        inputs.map((input) => {
            importFile(input);
        });

    });

});