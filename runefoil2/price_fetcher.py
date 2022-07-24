import datetime
import logging
import pymysql
import requests

# userAgent = "RuneLite/" + version + "-" + commit + (dirty ? "+" : "");

_conn = None


def _dbconn():
  global _conn
  if _conn is None:
    _conn = pymysql.connect(
      "mysql",
      "runelite",
      "ironmanbtw",
      cursorclass=pymysql.cursors.DictCursor
    )

  return _conn


def seed_data_from_internet(runelite_version):
  s = requests.Session()

  r = s.get(_prices_url(runelite_version))
  r.raise_for_status()

  all_prices = r.json()

  not_indb_count = 0
  indb_count = 0

  logging.info("seeding items table")

  dbconn = _dbconn()

  for i, item_price in enumerate(all_prices):
    try:
      with dbconn.cursor() as c:
        if not _select_item(item_price["id"], c):
          item = {
            "id": item_price["id"],
            "name": item_price["name"],
            "description": "not implemented",
          }

          _insert_item(item, c)
          indb = False
          not_indb_count += 1
        else:
          indb = True
          indb_count += 1
    except Exception:
      dbconn.rollback()
      raise

    logmethod = logging.debug
    if i % 50 == 1:
      logmethod = logging.info

    logmethod("Processed {} (id={}, progress={}/{}, indb={})".format(item_price["name"], item_price["id"], i + 1, len(all_prices), indb))

    if not indb:
      dbconn.commit()

  logging.info("items table seeded with {} items added to db and {} existing items".format(not_indb_count, indb_count))

  _update_prices_table_and_commit(all_prices)


def restore_data_from_dump():
  pass


def fetch_latest_information_from_internet(runelite_version):
  dbconn = _dbconn()

  with dbconn.cursor() as c:
    c.execute("SELECT COUNT(*) as cnt FROM `runelite`.`items`")
    row_count = c.fetchone()["cnt"]

  s = requests.Session()
  r = s.get(_prices_url(runelite_version))
  r.raise_for_status()
  all_prices = r.json()

  if len(all_prices) != row_count:
    logging.info("local cache has {} items, remote has {} items, calling seed instead.".format(row_count, len(all_prices)))
    seed_data_from_internet(runelite_version)
    return

  logging.info("only updating prices table as item list didn't change")
  _update_prices_table_and_commit(all_prices)


def _prices_url(runelite_version):
  return "https://api.runelite.net/runelite-{}/item/prices.js".format(runelite_version)


def _select_item(item_id, cursor):
  cursor.execute("SELECT * FROM `runelite`.`items` WHERE id = %s", (item_id, ))
  return cursor.fetchone()


def _insert_item(item, cursor):
  data = [
    ("id", "%s", item["id"]),
    ("name", "%s", item["name"]),
    ("description", "%s", item["description"]),
    ("type", "%s", "DEFAULT"),
  ]

  columns, subs, args = zip(*data)
  columns = ", ".join(columns)
  subs = ", ".join(subs)

  cursor.execute("INSERT INTO `runelite`.`items` ({}) values ({})".format(columns, subs), args)


def _update_prices_table_and_commit(all_prices):
  logging.info("updating prices table with {} entries".format(len(all_prices)))
  query = "REPLACE INTO `runelite`.`prices` (item, price, time, fetched_time) VALUES (%s, %s, %s, %s)"
  args = []

  # BUG: likely an issue with local timezone? Doesn't matter that much tho.
  fetched_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  for item_price in all_prices:
    # TODO: https://oldschool.runescape.wiki/w/RuneScape:Real-time_Prices
    # As of 1.7.3, the runelite api gives {"id":2,"name":"Cannonball","price":171,"wikiPrice":164}
    args.append([
      item_price["id"],
      item_price["wikiPrice"],
      fetched_time, # TODO: don't think this is right but it'll get around 1.7.3.
      fetched_time,
    ])

  dbconn = _dbconn()

  with dbconn.cursor() as c:
    rows_changed = c.executemany(query, args)  # The number here is wrong...

  dbconn.commit()
  logging.info("updated {} prices rows".format(rows_changed))
