from datetime import datetime
import requests
import json
import os


OSBUDDY_EXCHANGE_URL = "https://rsbuddy.com/exchange/summary.json"
RS_ITEM_URL = "https://services.runescape.com/m=itemdb_oldschool/api/catalogue/detail.json?item={}"


def fetch_osbuddy_summary(network=False) -> dict:
  if not network:
    with open("osbuddy_summary.json") as f:
      return json.load(f)

  r = requests.get(OSBUDDY_EXCHANGE_URL)
  return r.json()


def build_runelite_table_rows(osbuddy_summary: dict) -> dict:
  items = []
  prices = []

  now = datetime.now()
  now_timestamp = int(now.timestamp()) * 1000
  day_timestamp = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()) * 1000

  previous_items_cache = {}
  previous_prices_cache = {}

  if os.path.exists("items.txt"):
    with open("items.txt") as f:
      for line in f:
        item = json.loads(line.strip())
        previous_items_cache[item["id"]] = item

  if os.path.exists("prices.txt"):
    with open("prices.txt") as f:
      for line in f:
        item = json.loads(line.strip())
        previous_prices_cache[item["item"]] = item

  print("loaded previous cache: {} items and {} prices".format(len(previous_items_cache), len(previous_prices_cache)))
  if len(previous_items_cache) != len(previous_prices_cache):
    raise

  fitems = open("items.txt", "a")
  fprices = open("prices.txt", "a")

  try:
    i = 0
    for item_id, item_detail in sorted(osbuddy_summary.items(), key=lambda i: int(i[0])):
      i += 1
      item_id = int(item_id)
      item_price = item_detail["overall_average"]

      if item_id in previous_items_cache and item_id in previous_prices_cache:
        item = previous_items_cache[item_id]
        price = previous_prices_cache[item_id]
        cached = True
      else:
        url = RS_ITEM_URL.format(item_id)
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()["item"]

        # This dict is based on the `runelite`.`items` table.
        item = {
          "id": item_id,
          "name": data["name"],
          "description": data["description"],
          "type": data["type"].upper(),
        }

        # This dict is based on the `runelite`.`prices` table.
        price = {
          "item": item_id,
          "price": item_price,
          "time": day_timestamp,
          "fetched_time": now_timestamp,
        }
        print(json.dumps(item), file=fitems, flush=True)
        print(json.dumps(price), file=fprices, flush=True)

        cached = False

      print("fetched item {} (id={}\tprogress={}/{}\tcached={})".format(item_detail["name"], item_id, i, len(osbuddy_summary), cached), flush=True)

      items.append(item)
      prices.append(price)
  finally:
    fitems.close()
    fprices.close()

  tables = {"items": items, "prices": prices}
  return tables


def main():
  s = fetch_osbuddy_summary()
  tables = build_runelite_table_rows(s)
  with open("test.json", "w") as f:
    json.dump(tables, f)


main()
