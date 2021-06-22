# tyosis-import

This tools imports EOF price data from your broker into a redis database, so you can build a price database that you can backtest your strategy.

## data structure
KEY                 FIELD               VALUE
[PREFIX]SYMBOL      YYYYMMDD          {"O": XX.XXX, "C": XX.XXX, "H": XX.XXX, "L": XX.XXX}

## Usage
```nodejs
tyosis-import [options] inputs

avaialbe options:
                 
                 --data-format YYYYMMDD
                 
                 --symbol-index 0
                 --date-index   1
                 --open-index   2
                 --high-index   3
                 --low-index    4
                 --close-index  5
                 --volume-index 6
                 
                 --database     0
                 
                 --key-prefix   a-key-prefix
```

## Examples

The below command imports the EOF price data provided CommSec into database number 11.

```bash
tyosis-import --key-prefix "asx:price:" --database 11 ./data/commsec/2020/MarketP_21102020.txt
```

If the data format in the file is already converted into YYYYMMDD, use the following command:
```bash
tyosis-import --key-prefix "asx:price:" --convert-date no ./data/2020/21102020.txt
```

## Notes
The date in the EOF data from CommSec is in a format of "dd MMM yyyy" which can be regonised by the tool automatically. If the date format in m

## Maintainer

[Eric Tang](https://twitter.com/_e_tang) @ [TYO Lab](http://tyo.com.au)