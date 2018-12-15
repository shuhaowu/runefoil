import datetime
import logging
import os
import pymysql
import requests
import sys
import time

from .updater import get_local_version

UA = "okhttp/3.7.0"
RL_VERSION = get_local_version()
RL_PRICES_URL = "https://api.runelite.net/runelite-{}/item/prices.json".format(RL_VERSION)
RL_ITEM_URL = "https://api.runelite.net/runelite-" + RL_VERSION + "/item/{}"
RS_ITEM_ICON_URL = "https://secure.runescape.com/m=itemdb_oldschool/1544700611648_obj_sprite.gif?id={}"
RS_ITEM_ICON_LARGE_URL = "https://secure.runescape.com/m=itemdb_oldschool/1544700611648_obj_big.gif?id={}"
RL_ITEM_ICON_URL = RL_ITEM_URL + "/icon"
RL_ITEM_ICON_LARGE_URL = RL_ITEM_ICON_URL + "/large"


class PriceFetcher(object):
  def __init__(self, rate_limit=1):
    logging.basicConfig(format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG)
    self.s = requests.Session()
    self.s.headers.update({"User-Agent": UA})
    self.rate_limit = rate_limit

    self.dbconn = pymysql.connect(
      "127.0.0.1",
      "runelite",
      "ironmanbtw",
      cursorclass=pymysql.cursors.DictCursor
    )

  def __getattr__(self, attr):
    return getattr(self.s, attr)

  def seed(self):
    r = self.get(RL_PRICES_URL)
    r.raise_for_status()
    all_prices = r.json()

    last_processed = datetime.datetime.now()

    for i, item_price in enumerate(all_prices):
      try:
        with self.dbconn.cursor() as c:
          if not self._select_item(item_price["id"], c):
            r = self.get(RL_ITEM_URL.format(item_price["id"]))
            r.raise_for_status()
            item = r.json()

            r = self.get(RS_ITEM_ICON_URL.format(item_price["id"]))
            if r.status_code == 404:
              item["icon"] = None
            else:
              r.raise_for_status()
              item["icon"] = r.content

            r = self.get(RS_ITEM_ICON_LARGE_URL.format(item_price["id"]))
            if r.status_code == 404:
              item["icon_large"] = None
            else:
              r.raise_for_status()
              item["icon_large"] = r.content

            self._insert_item(item, c)
            indb = False
          else:
            indb = True

          self._replace_price(item_price, c)
      except Exception:
        self.dbconn.rollback()
        raise

      self.dbconn.commit()
      logging.info("Processed {} (id={}, progress={}/{}, indb={})".format(item_price["name"], item_price["id"], i + 1, len(all_prices), indb))

      if not indb:
        while (datetime.datetime.now() - last_processed).total_seconds() < self.rate_limit:
          time.sleep(0.02)

      last_processed = datetime.datetime.now()

  def _select_item(self, item_id, cursor):
    cursor.execute("SELECT * FROM `runelite`.`items` WHERE id = %s", (item_id, ))
    return cursor.fetchone()

  def _insert_item(self, item, cursor):
    data = [
      ("id", "%s", item["id"]),
      ("name", "%s", item["name"]),
      ("description", "%s", item["description"]),
      ("type", "%s", item["type"].upper()),
      ("icon", "%s", None if item["icon"] is None else pymysql.Binary(item["icon"])),
      ("icon_large", "%s", None if item["icon_large"] is None else pymysql.Binary(item["icon_large"])),
    ]

    columns, subs, args = zip(*data)
    columns = ", ".join(columns)
    subs = ", ".join(subs)

    cursor.execute("INSERT INTO `runelite`.`items` ({}) values ({})".format(columns, subs), args)

  def _replace_price(self, price, cursor):
    # BUG: likely an issue with local timezone? Doesn't matter that much tho.
    time = datetime.datetime.fromtimestamp(price["time"]["epochSecond"])
    fetched_time = datetime.datetime.now()
    data = (
      ("item", "%s", price["id"]),
      ("price", "%s", price["price"]),
      ("time", "%s", time.strftime("%Y-%m-%d %H:%M:%S")),
      ("fetched_time", "%s", fetched_time.strftime("%Y-%m-%d %H:%M:%S"))
    )

    columns, subs, args = zip(*data)
    columns = ", ".join(columns)
    subs = ", ".join(subs)

    cursor.execute("REPLACE INTO `runelite`.`prices` ({}) values ({})".format(columns, subs), args)


def main():
  if RL_VERSION == "none":
    raise RuntimeError("must first install runelite before running this")

  logging.basicConfig(format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG)
  if len(sys.argv) < 2:
    print("error: must specify action as either seed or fetch", file=sys.stderr)
    sys.exit(1)

  action = sys.argv[1].lower()
  rate_limit = float(os.environ.get("RATE_LIMIT", 1))

  fetcher = PriceFetcher(rate_limit=rate_limit)
  f = getattr(fetcher, action, None)
  if f is None:
    print("error: {} is not valid. it must be either seed or fetch.".format(action), file=sys.stderr)
    sys.exit(1)

  f()
