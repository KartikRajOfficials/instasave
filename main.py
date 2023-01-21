import asyncio
import logging
import os

import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.emoji import emojize
from instalooter.looters import PostLooter

logging.basicConfig(level=logging.ERROR)

API_TOKEN = os.environ['5963970181:AAHvX9KJ84tfiRGDARzsDpFm5-DCysusvzM']

HELP_MESSAGE = \
'''
Hello and welcome!


Submit a link from Instagram!

@Global_Chat_group_1 join here 
'''

ERROR_MESSAGE = \
'''
The link you sent is incorrect or this account has been closed.
'''

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


def get_links(media, looter):
    if media.get('__typename') == 'GraphSidecar':
        media = looter.get_post_info(media['shortcode'])
        nodes = [e['node'] for e in media['edge_sidecar_to_children']['edges']]
        return [n.get('video_url') or n.get('display_url') for n in nodes]
    elif media['is_video']:
        media = looter.get_post_info(media['shortcode'])
        return [media['video_url']]
    else:
        return [media['display_url']]


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(HELP_MESSAGE)


@dp.message_handler()
@dp.throttled(rate=1)
async def send_media(message: types.Message):
    try:
        looter = PostLooter(message.text, get_videos=True)
        edges = looter.info['edge_media_to_caption']['edges']
    except (ValueError, KeyError):
        await message.answer(emojize(ERROR_MESSAGE))
        return

    media = types.MediaGroup()
    for m in looter.medias():
        for link in get_links(m, looter):
            if '.mp4' in link:
                media.attach_video(link)
            else:
                media.attach_photo(link)

    await message.answer_media_group(media=media)

    try:
        description = edges[0]['node']['text']
        await message.answer(description)
    except IndexError:
        await message.answer('<i>No description.</i>', parse_mode=types.ParseMode.HTML)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
