import datetime
import logging
import os
import pymysql
import requests
import sys
import time

from . import constants as c
from .updater import get_local_version, system

UA = "okhttp/3.7.0"
RL_VERSION = get_local_version()
RL_PRICES_URL = "https://api.runelite.net/runelite-{}/item/prices.json".format(RL_VERSION)
RL_ITEM_URL = "https://api.runelite.net/runelite-" + RL_VERSION + "/item/{}"
RS_ITEM_ICON_URL = "https://secure.runescape.com/m=itemdb_oldschool/1544700611648_obj_sprite.gif?id={}"
RS_ITEM_ICON_LARGE_URL = "https://secure.runescape.com/m=itemdb_oldschool/1544700611648_obj_big.gif?id={}"

DB_USERNAME = "runelite"
DB_PASSWORD = "ironmanbtw"
DB_DUMP_PATH = os.path.join(c.FILES_PATH, "items-prices-db-dump.sql.gz")


class PriceFetcher(object):
  def __init__(self, rate_limit=1):
    self.s = requests.Session()
    self.s.headers.update({"User-Agent": UA})
    self.rate_limit = rate_limit

    self.dbconn = pymysql.connect(
      "127.0.0.1",
      DB_USERNAME,
      DB_PASSWORD,
      cursorclass=pymysql.cursors.DictCursor
    )

  def __getattr__(self, attr):
    return getattr(self.s, attr)

  def fetch(self):
    with self.dbconn.cursor() as c:
      c.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'runelite' AND table_name = 'items'")
      r = c.fetchone()
      if r == 0:
        logging.error("database not created yet, not fetching!")
        return

      c.execute("SELECT COUNT(*) as cnt FROM `runelite`.`items`")
      row_count = c.fetchone()["cnt"]

    r = self.get(RL_PRICES_URL)
    r.raise_for_status()
    all_prices = r.json()

    if len(all_prices) != row_count:
      logging.info("local cache has {} items, remote has {} items, calling seed instead.".format(row_count, len(all_prices)))
      self.seed(all_prices=all_prices)
      return

    self._update_prices_table_and_commit(all_prices)

  def seed(self, all_prices=None):
    if all_prices is None:
      r = self.get(RL_PRICES_URL)
      r.raise_for_status()
      all_prices = r.json()

    last_processed = datetime.datetime.now()

    not_indb_count = 0
    indb_count = 0

    logging.info("seeding items table")

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
            not_indb_count += 1
          else:
            indb = True
            indb_count += 1
      except Exception:
        self.dbconn.rollback()
        raise

      logmethod = logging.debug
      if i % 100 == 1:
        logmethod = logging.info

      logmethod("Processed {} (id={}, progress={}/{}, indb={})".format(item_price["name"], item_price["id"], i + 1, len(all_prices), indb))

      if not indb:
        self.dbconn.commit()
        while (datetime.datetime.now() - last_processed).total_seconds() < self.rate_limit:
          time.sleep(0.02)

      last_processed = datetime.datetime.now()

    logging.info("items table seeded with {} items added to db and {} existing items".format(not_indb_count, indb_count))

    self._update_prices_table_and_commit(all_prices)

  def restore(self):
    system("gunzip -c {} | mysql -h 127.0.0.1 -u {} -p{} runelite".format(DB_DUMP_PATH, DB_USERNAME, DB_PASSWORD))

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

  def _update_prices_table_and_commit(self, all_prices):
    logging.info("updating prices table with {} entries".format(len(all_prices)))
    query = "REPLACE INTO `runelite`.`prices` (item, price, time, fetched_time) VALUES (%s, %s, %s, %s)"
    args = []

    # BUG: likely an issue with local timezone? Doesn't matter that much tho.
    fetched_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for item_price in all_prices:
      time = datetime.datetime.fromtimestamp(item_price["time"]["seconds"]).strftime("%Y-%m-%d %H:%M:%S")
      args.append([
        item_price["id"],
        item_price["price"],
        time,
        fetched_time,
      ])

    with self.dbconn.cursor() as c:
      rows_changed = c.executemany(query, args)

    self.dbconn.commit()
    logging.info("updated {} prices rows".format(rows_changed))


def main():
  if RL_VERSION == "none":
    raise RuntimeError("must first install runelite before running this")

  logging.basicConfig(format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
  if len(sys.argv) < 2:
    print("error: must specify action as either restore, seed or fetch", file=sys.stderr)
    sys.exit(1)

  action = sys.argv[1].lower()
  rate_limit = float(os.environ.get("RATE_LIMIT", 1))

  fetcher = PriceFetcher(rate_limit=rate_limit)
  f = getattr(fetcher, action, None)
  if f is None:
    print("error: {} is not valid. it must be either restore, seed, or fetch.".format(action), file=sys.stderr)
    sys.exit(1)

  f()
