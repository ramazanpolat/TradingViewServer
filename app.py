from datetime import datetime
from typing import List
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from prodict import Prodict
from sipro.pricecandle import PriceCandle

import logging

#log = logging.getLogger('werkzeug')
#log.setLevel(logging.DEBUG)

app = Flask(__name__,
            static_url_path='')
CORS(app)

datetime_format1 = "%Y-%m-%dT%H:%M:%S"


def dt(dt_or_ts):
    if type(dt_or_ts) == float:
        ts = int(dt_or_ts)

    if isinstance(dt_or_ts, datetime):
        ts = int(dt_or_ts.timestamp())
    return ts


class HitBTCCandle(Prodict):
    timestamp: str
    open: float
    close: float
    min: float
    max: float
    volume: float
    volumeQuote: float

    def to_price_candle(self, period):
        c = PriceCandle()
        c.datetime = datetime.strptime(self.timestamp.split(".")[0], datetime_format1).replace(tzinfo=None)
        c.ts = int(c.datetime.timestamp())
        c.interval = period
        c.open = self.open
        c.close = self.close
        c.high = self.max
        c.low = self.min
        c.volume = self.volume
        c.base_volume = self.volumeQuote
        return c


class HitBTC:
    def __init__(self):
        # 1, 3, 5, 15
        self.base_url = "https://api.hitbtc.com/api/2/public/candles/{}{}?period=M{}&limit={}"

    def get_candles(self, base, quote, period: int, limit: int = 1000):
        url = self.base_url.format(base, quote, period, limit)
        candle_list_dict = requests.get(url).json()
        candle_list: List[PriceCandle] = []
        for c in candle_list_dict:
            hit_candle = HitBTCCandle.from_dict(c)
            price_candle = hit_candle.to_price_candle(period)
            price_candle.exchange = 'hitbtc'
            price_candle.base = base
            price_candle.quote = quote
            candle_list.append(price_candle)

        # print(f"len(candle_list)={len(candle_list)}")
        # if len(candle_list) > 0:
        #     print(f"Last ts     :{candle_list[-1].ts}")
        #     print(f"Last dt     :{str(candle_list[-1].datetime)}")

        return candle_list

    # def get_candles_range(self, base, quote, period: int, from_datetime, to_datetime):
    #     all_candles = self.get_candles(base=base, quote=quote, period=period, limit=1000)
    #     print(f"2-len(candle_list)={len(all_candles)}")
    #     return [c for c in all_candles if from_datetime <= c.datetime <= to_datetime]

    def get_candles_range_ts(self, base, quote, period: int, from_ts, to_ts):

        from_dt = str(datetime.fromtimestamp(from_ts)) + f"\t{from_ts}"
        to_dt = str(datetime.fromtimestamp(to_ts)) + f"\t{to_ts}"
        print(f"Asking for\nFrom         :{from_dt}\nTo           :{to_dt}")

        now_ts = int(datetime.now().timestamp())
        now_dt = str(datetime.fromtimestamp(now_ts))
        now_dt_utc = str(datetime.utcfromtimestamp(now_ts))

        utcnow_ts = int(datetime.utcnow().timestamp())
        utcnow_dt = str(datetime.fromtimestamp(utcnow_ts))
        utcnow_dt_utc = str(datetime.utcfromtimestamp(utcnow_ts))

        s1 = f"now_ts       :{now_ts}\n"
        s1 += f"utcnow_ts    :{utcnow_ts}\n"
        s1 += f"now_dt       :{now_dt}\n"
        s1 += f"utcnow_dt    :{utcnow_dt}\n"
        s1 += f"now_dt_utc   :{now_dt_utc}\n"
        s1 += f"utcnow_dt_utc:{utcnow_dt_utc}"

        # print(s1)

        all_candles = self.get_candles(base=base, quote=quote, period=period, limit=1000)

        last_dt = all_candles[-1].datetime
        last_ts = all_candles[-1].ts
        last_ts_2_dt = datetime.fromtimestamp(last_ts)
        print(f"Last dt      :{str(last_dt)}")
        print(f"Last ts      :{last_ts}")
        print(f"Last ts 2 dt :{str(last_ts_2_dt)}")
        # for c in all_candles:
        #     print(c.display3())
        # print(f"3-len(candle_list)={len(all_candles)}")
        sub_candles = [c for c in all_candles if from_ts <= c.ts <= to_ts]

        print(f"\tSending bars = {len(sub_candles)}")

        # for c in sub_candles:
        #     print(c.display())

        return sub_candles

    def to_UDF(self, candles: List[PriceCandle]):
        result = dict(
            s="ok",
            t=[],
            c=[],
            o=[],
            h=[],
            l=[],
            v=[],
        )

        for candle in candles:
            result['t'].append(int(candle.ts))
            result['c'].append(candle.close)
            result['o'].append(candle.open)
            result['h'].append(candle.high)
            result['l'].append(candle.low)
            result['v'].append(candle.base_volume)

        # print(f"\tSending bars = {len(candles)}")
        # if len(candles) > 0:
        #     print(f"\tStart ts:{candles[0].ts}\tdt:{str(candles[0].datetime)}")
        #     print(f"\tEnd   ts:{candles[-1].ts}\tdt:{str(candles[-1].datetime)}")

        return result


@app.route('/config')
def config():
    results = dict(
        supports_search=True,
        supports_group_request=False,
        supported_resolutions=["1", "3", "5", "15", "30"],
        supports_marks=False,
        supports_time=True)

    return jsonify(results)


EXCHANGE = HitBTC()


@app.route('/history')
def history():
    symbol = request.args.get('symbol')
    resolution = int(request.args.get('resolution'))
    from_ts = int(request.args.get('from'))
    to_ts = int(request.args.get('to'))

    candles = EXCHANGE.get_candles_range_ts(base='BTC', quote='USD', period=resolution, from_ts=from_ts, to_ts=to_ts)
    response = EXCHANGE.to_UDF(candles)

    return jsonify(response)


@app.route('/symbols')
def symbols():
    symbol = request.args.get('symbol')

    results = {}

    results["name"] = symbol
    results["ticker"] = "BTC/USD"
    results["description"] = "BTC/USD"
    results["type"] = ""
    results["session"] = "24x7"
    results["exchange"] = "HitBTC"
    results["listed_exchange"] = "HitBTC"
    # results["timezone"] = "Europe/Istanbul"
    results["minmov"] = 1
    results["minmove2"] = 0
    results["pricescale"] = 100000
    results["fractional"] = False
    results["has_intraday"] = True
    # results["supported_resolutions"] = ["1", "3", "5", "15", "30"],
    # results["intraday_multipliers"] = []
    results["has_seconds"] = False
    results["seconds_multipliers"] = ""
    results["has_daily"] = True
    results["has_weekly_and_monthly"] = False
    results["has_empty_bars"] = True
    results["force_session_rebuild"] = ""
    results["has_no_volume"] = False
    results["volume_precision"] = ""
    results["data_status"] = ""
    results["expired"] = ""
    results["expiration_date"] = ""
    results["sector"] = ""
    results["industry"] = ""
    results["currency_code"] = ""

    return jsonify(results)


@app.route('/time')
def time():
    return str(int(datetime.utcnow().timestamp()))


@app.route('/hello')
def hello_world():
    return 'Hello World!'


@app.route('/<path:path>')
def static_file(path):
    return app.send_static_file(path)


@app.route('/')
def projects():
    return render_template("index.html", title='Projects')


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
