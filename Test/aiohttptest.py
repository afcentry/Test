#coding:utf-8

import aiohttp
import asyncio

@asyncio.coroutine
async def getPage(url,res_list):
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.github.com/events') as resp:
            print(resp.status)
            print(await resp.text())