import aiohttp
import asyncio
import platform
import sys
from datetime import datetime, timedelta

from pprint import pprint as print

URL_PRIVAT_BANK = "https://api.privatbank.ua/p24api/exchange_rates?json&date="
result_list = []


async def create_list_urls(args: str = None):
    today = datetime.today()
    urls = [URL_PRIVAT_BANK + today.strftime("%d.%m.%Y")]
    if args and int(args) > 10:
        args = 10
    if args:
        for i in range(1, int(args)):
            new_date = today - timedelta(days=i)
            formatted_date = new_date.strftime("%d.%m.%Y")
            urls.append(URL_PRIVAT_BANK + formatted_date)
    return urls


class HttpError(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
        super().__init__(self.message)
        self.log_error()

    def __str__(self):
        return f"CustomError: {self.message}. Error code: {self.code}"

    def log_error(self):
        with open("error.log", "a") as f:
            f.write(f"Error: {self.message}. Error code: {self.code}\n")


async def parser_json(json_dict: dict) -> dict:
    result_dict = {}
    value_dict = {}
    date = json_dict.get("date")
    data_list = json_dict.get("exchangeRate")

    for i in data_list:
        if i.get("currency") in ["EUR", "USD"]:
            value = {
                i.get("currency"): {
                    "sale": i.get("saleRateNB"),
                    "purchase": i.get("purchaseRateNB"),
                }
            }
            value_dict.update(value)
    result_dict[date] = value_dict
    return result_dict


async def request(url: str, parser):
    async with aiohttp.ClientSession() as session:
        print(f"Starting {url}")
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    result = await parser(result)
                    result_list.append(result)
                else:
                    raise HttpError(
                        f"Error status: {resp.status} for {url}", resp.status
                    )
        except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
            raise HttpError(f"Connection error: {url}", str(err))


async def main(args):
    urls = await create_list_urls(args)
    try:
        await asyncio.gather(*[request(url, parser_json) for url in urls])
    except HttpError as err:
        print(err)


if __name__ == "__main__":
    args = sys.argv[1]
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(args))
    print(result_list)
