import logging
from aiogram import (
    Bot,
    Dispatcher,
    types
)
from aiogram.utils.executor import Executor

from fastapi import (
    FastAPI,
    Request
)
import asyncio
import uvicorn

from config import *
import api
import utils

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot)


def parse_args(message):
    return message.get_args().replace('  ', ' ').split(' ')


@dispatcher.message_handler(commands=['register'])
async def register_handler(message: types.Message):
    args = parse_args(message)
    try:
        await message.delete()
    except:
        pass
    if len(args) != 2:
        await bot.send_message(
            chat_id=message.chat.id,
            text=f'❌ @{message.from_user.username} Invalid arguments.\n'
                 ' Usage: `/register <username> <password>`',
            parse_mode='Markdown'
        )
        return
    else:
        username, password = args
        if len(username) < 3 or len(username) > 25:
            await bot.send_message(
                chat_id=message.chat.id,
                text=f'❌ @{message.from_user.username}\n'
                     f'Command usage incorrect: Username must be between 3 and 25 characters long.'
            )
            return
        elif len(password) < 7 or len(password) > 30:
            await bot.send_message(
                chat_id=message.chat.id,
                text=f'❌ @{message.from_user.username}\n'
                     f'Command usage incorrect: Password must be between 7 and 30 characters long.'
            )
            return
        else:
            # Perform register
            try:
                response_json = await api.user_register(
                    username=username,
                    im_id=message.from_user.id,
                    password_hash=utils.calculate_password_hash(password)
                )
                if 'success' in response_json:
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=f'✅ **{username}** (@{message.from_user.username}) '
                             f'was successfully registered, now you can start playing',
                        parse_mode='Markdown'
                    )
                else:
                    if response_json['error_type'] == '035':
                        await bot.send_message(
                            chat_id=message.chat.id,
                            text=f'❌ @{message.from_user.username}, you are already registered.\n'
                                 f'Your username is: **{response_json["username"]}**',
                            parse_mode='Markdown'
                        )
                    elif response_json['error_type'] == '036':
                        await bot.send_message(
                            chat_id=message.chat.id,
                            text=f'❌ @{message.from_user.username}, this username is already taken.',
                        )
                    else:
                        await bot.send_message(
                            chat_id=message.chat.id,
                            text=f"❌ @{message.from_user.username}\n"
                                 f"Unknown error occurred.\n"
                                 f"{response_json['error_type']} - {response_json['message']}"
                        )
            except Exception as e:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=f'❌ @{message.from_user.username}\n'
                         f'Error occurred while registering: {e}'
                )


@dispatcher.message_handler(commands=['change_password'])
async def change_password_handler(message: types.Message):
    args = parse_args(message)
    try:
        await message.delete()
    except:
        pass
    if len(args) != 1:
        await bot.send_message(
            chat_id=message.chat.id,
            text=f'❌ @{message.from_user.username} Invalid arguments.\n'
                 ' Usage: `/change_password <password>`',
            parse_mode='Markdown'
        )
        return
    else:
        password: str = args[0]
        if len(password) < 7 or len(password) > 30:
            await bot.send_message(
                chat_id=message.chat.id,
                text=f'❌ @{message.from_user.username}\n'
                     f'Command usage incorrect: Password must be between 7 and 30 characters long.'
            )
            return
        else:
            try:
                response_json = await api.update_password(
                    user_identifier=str(message.from_user.id),
                    im_id=message.from_user.id,
                    password_hash=utils.calculate_password_hash(password)
                )
                if 'success' in response_json:
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=f'✅ @{message.from_user.username}\n'
                             f'Password changed successfully.'
                    )
                else:
                    if response_json['error_type'] == '006':
                        await bot.send_message(
                            chat_id=message.chat.id,
                            text=f'❌ @{message.from_user.username},\n'
                                 f'You have not registered yet. Use `/register` command to register.',
                            parse_mode='Markdown'
                        )
                    else:
                        await bot.send_message(
                            chat_id=message.chat.id,
                            text=f"❌ @{message.from_user.username}\n"
                                 f"Unknown error occurred.\n"
                                 f"{response_json['error_type']} - {response_json['message']}"
                        )
            except Exception as e:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=f'❌ @{message.from_user.username}\n'
                         f'Error occurred while changing password: {e}'
                )


@dispatcher.message_handler(commands=['levels'])
async def levels_handler(message: types.Message):
    reply_message = await message.reply(
        '⏰ Loading ...'
    )
    user_identifier: str = message.get_args()
    user_identifier: str = str(message.from_user.id) if user_identifier == '' else user_identifier
    response_texts: list[str] = []
    user_info_response = await api.user_info(
        user_identifier=user_identifier
    )
    if 'result' not in user_info_response:
        await message.reply(
            f'❌ {"This user" if user_identifier != str(message.from_user.id) else "You"} are not registered yet.'
        )
        return
    else:
        user_info = user_info_response['result']
        response_texts.append(
            f"**{user_info['username']}** (@{message.from_user.username})"
            + f'{f"**👮 Stage Moderator**" if user_info["is_mod"] else ""}'
            + f'{f"**🚀 Booster**" if user_info["is_booster"] else ""}'
        )
        response_texts.append(f"📤 Uploads: {user_info['uploads']}")
        response_texts.append('⏰ Loading...')

        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=reply_message.message_id,
            text='\n'.join(response_texts),
            parse_mode='Markdown'
        )
        response_texts.pop()

        username = user_info['username']
        auth_code = await api.login_session(API_TOKEN)
        levels = await api.get_user_levels(
            username=username,
            auth_code=auth_code,
            rows_perpage=user_info['uploads'] + 1
        )
        for level in levels:
            response_texts.append(
                f"- {level['name']} "
                f"{'✨ ' if level['featured'] == 1 else ''}"
                f"`{level['id']}` | "
                f"❤️ {level['likes']} "
                f"💙 {level['dislikes']}"
            )
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=reply_message.message_id,
            text='\n'.join(response_texts),
            parse_mode='Markdown'
        )
        return


@dispatcher.message_handler(commands=['server_stats'])
async def server_stats_handler(message: types.Message):
    server_stats = await api.server_stats()
    reply_message = await message.reply(
        '⏰ Loading ...'
    )
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=reply_message.message_id,
        text=(
            f'🗄️ **Server Statistics**\n'
            f'🐧 OS: {server_stats.os}\n'
            f'🐍 Python version: {server_stats.python}\n'
            f'👥 Player count: {server_stats.player_count}\n'
            f'🌏 Level count: {server_stats.level_count}\n'
            f'🕰️ Uptime: {int(server_stats.uptime / 60)} minutes\n'
            f'📊 Connection per minute: {server_stats.connection_per_minute}'
        ).replace('_', '\\_'),
        parse_mode='Markdown'
    )
    return


def level_details_to_string(level: dict, leading_char: str) -> str:
    clears: int = level['victorias']
    attempts: int = level['intentos']
    clear_rate: str = str(round(clears / attempts * 100, 2)) + '%'
    return (
        f"{leading_char} **{level['name']}**{' ✨' if level['featured'] == 1 else ''}\n"
        f"👤 Author **{level['author']}**\n"
        f"ID: `{level['id']}`\n"
        f"🏷️ {level['etiquetas']}\n"
        f"❤️ {level['likes']} | 💙 {level['dislikes']}\n"
        f"⛳ {clears} / 🎮 {attempts} ({clear_rate})\n"
    )


@dispatcher.message_handler(commands=['query_level'])
async def query_level_handler(message: types.Message):
    def prettify_level_id(raw_level_id: str):
        return raw_level_id[0:4] + '-' + raw_level_id[4:8] + '-' + raw_level_id[8:12] + '-' + raw_level_id[12:16]

    level_id = message.get_args()
    if level_id == '':
        await message.reply(
            '❌ Please provide a level ID.'
        )
        return
    elif '-' not in level_id:
        level_id = prettify_level_id(level_id)
    else:
        level_id = level_id.upper()
    try:
        auth_code = await api.login_session(token=API_TOKEN)
        response_json = await api.query_level(
            level_id=level_id,
            auth_code=auth_code
        )
        if 'error_type' in response_json:
            await message.reply(
                f'❌ Level not found.'
            )
        else:
            level_data: dict = response_json['result']
            await message.reply(
                level_details_to_string(level_data, '🔍')
            )
    except Exception as e:
        await message.reply(
            f'❌ Error: {e}'
        )


@dispatcher.message_handler(commands=['random_level'])
async def random_level_handler(message: types.Message):
    difficulty = message.get_args()
    if difficulty == '':
        difficulty = None
    else:
        difficulty_ids: dict[str, int] = {
            # SMM1 风格的难度名
            'easy': 0, 'normal': 1, 'expert': 2, 'super expert': 3,
            # SMM2 风格的难度名
            'hard': 2, 'very hard': 3,
            # TGRCode API 风格的难度 ID
            'e': 0, 'n': 1, 'ex': 2, 'sex': 3,
            # SMMWE API 风格的难度 ID
            '0': 0, '1': 1, '2': 2, '3': 3
        }
        if difficulty.lower() not in difficulty_ids:
            await message.reply(
                '❌ Invalid difficulty.\n'
                'Valid difficulties: `easy`, `normal`, `expert`, `super expert`',
                parse_mode='Markdown'
            )
            return
        difficulty = difficulty_ids[difficulty.lower()]
    try:
        auth_code = await api.login_session(
            token=API_TOKEN
        )
        response_json = await api.random_level(
            auth_code=auth_code,
            difficulty=difficulty
        )
        level_data: dict = response_json['result']
        await message.reply(
            level_details_to_string(level_data, '🎲')
        )
    except Exception as e:
        await message.reply(
            f'❌ Error: {e}'
        )


@dispatcher.message_handler(commands=['permission'])
async def permission_handler(message: types.Message):
    if (await bot.get_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id
    )).status != 'creator':
        await message.reply(
            '❌ Permission denied.'
        )
        return
    args = parse_args(message)
    if len(args) != 3:
        await message.reply(
            '❌ Invalid arguments.\n'
            'Usage: `/permission <Username\\|ID> <Permission> <true\\|false>`',
            parse_mode='Markdown'
        )
        return
    user_identifier: str = args[0]
    permission: str = args[1]
    value: str = args[2]
    if value.lower() not in ['true', 'false']:
        await message.reply(
            '❌ Invalid value.\n'
            'Usage: `/permission <Username\\|ID> <Permission> <true\\|false>`',
            parse_mode='Markdown'
        )
        return
    value: bool = value.lower() == 'true'
    if permission not in ['mod', 'admin', 'booster', 'valid', 'banned']:
        await message.reply(
            '❌ Invalid permission.\n'
            'Valid permissions: `mod`, `admin`, `booster`, `valid`, `banned`',
            parse_mode='Markdown'
        )
        return
    try:
        response_json = await api.update_permission(
            user_identifier=user_identifier,
            permission=permission,
            value=value
        )
        if 'success' in response_json:
            await message.reply(
                f'✅ Successfully updated permission for `{response_json["username"]}`.',
                parse_mode='Markdown'
            )
        else:
            await message.reply(
                f'❌ Failed to update permission.\n'
                f'{response_json["error_type"]} - {response_json["message"]}'
            )
    except Exception as e:
        await message.reply(
            f'❌ Error: {e}'
        )


@dispatcher.message_handler(commands=['ban'])
async def ban_handler(message: types.Message):
    if (await bot.get_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id
    )).status not in ['creator', 'administrator']:
        await message.reply(
            '❌ Permission denied.'
        )
        return
    user_identifier: str = message.get_args()
    if user_identifier == '':
        await message.reply(
            '❌ Invalid arguments.\n'
            'Usage: `/ban <Username\\|ID>`',
            parse_mode='Markdown'
        )
        return
    try:
        response_json = await api.update_permission(
            user_identifier=user_identifier,
            permission='banned',
            value=True
        )
        if 'success' in response_json:
            await message.reply(
                f'✅ Successfully banned `{response_json["username"]}`.',
                parse_mode='Markdown'
            )
        else:
            await message.reply(
                f'❌ Failed to ban.\n'
                f'{response_json["error_type"]} - {response_json["message"]}'
            )
    except Exception as e:
        await message.reply(
            f'❌ Error: {e}'
        )


@dispatcher.message_handler(commands=['unban'])
async def unban_handler(message: types.Message):
    if (await bot.get_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id
    )).status not in ['creator', 'administrator']:
        await message.reply(
            '❌ Permission denied.'
        )
        return
    user_identifier: str = message.get_args()
    if user_identifier == '':
        await message.reply(
            '❌ Invalid arguments.\n'
            'Usage: `/unban <Username\\|ID>`',
            parse_mode='Markdown'
        )
        return
    try:
        response_json = await api.update_permission(
            user_identifier=user_identifier,
            permission='banned',
            value=False
        )
        if 'success' in response_json:
            await message.reply(
                f'✅ Successfully unbanned `{response_json["username"]}`.',
                parse_mode='Markdown'
            )
        else:
            await message.reply(
                f'❌ Failed to unban.\n'
                f'{response_json["error_type"]} - {response_json["message"]}'
            )
    except Exception as e:
        await message.reply(
            f'❌ Error: {e}'
        )


'''
@dispatcher.message_handler(commands=['get_id'])
async def get_id(message: types.Message):
    await message.reply(
        message.chat.id
    )
'''

app = FastAPI()


@app.on_event('startup')
async def startup_event():
    await dispatcher.skip_updates()
    asyncio.create_task(
        dispatcher.start_polling()
    )


@app.on_event('shutdown')
async def shutdown_event():
    await dispatcher.stop_polling()


@app.post('/enginetribe')
async def enginetribe_payload(request: Request):
    webhook: dict = await request.json()
    message: str = ''
    match webhook["type"]:
        case 'new_arrival':  # new arrival
            message = f'📤 {webhook["author"]} uploaded a new level: {webhook["level_name"]}\n' \
                      f'ID: {webhook["level_id"]}'
        case 'new_featured':  # new featured
            message = f'🌟 {webhook["level_name"]} of {webhook["author"]} ' \
                      f'has been added to the featured levels, come and play!\n' \
                      f'ID: {webhook["level_id"]}'
        case 'permission_change':
            permission_name = {'booster': 'booster', 'mod': 'stage moderator'}[webhook['permission']]
            message = f"{'🤗' if webhook['value'] else '😥'} " \
                      f"{webhook['username']} {'gained' if webhook['value'] else 'lost'} " \
                      f"{permission_name} role of Engine Tribe!"
        case _:
            if 'likes' in webhook["type"]:  # 10/100/1000 likes
                message = f'🎉 Congratulations, {webhook["author"]}\'s level {webhook["level_name"]} has gained ' \
                          f'{webhook["type"].replace("_likes", "")} likes!\n' \
                          f'ID: {webhook["level_id"]}'
            if 'plays' in webhook["type"]:  # 100/1000 plays
                message = f'🎉 Congratulations, {webhook["author"]}\'s level {webhook["level_name"]} has been played ' \
                          f'{webhook["type"].replace("_plays", "")} times!\n' \
                          f'ID: {webhook["level_id"]}'
            if 'deaths' in webhook["type"]:  # 100/1000 deaths
                message = f'🔪 {webhook["author"]}\'s level {webhook["level_name"]} has obtained ' \
                          f'{webhook["type"].replace("_deaths", "")} deaths, come and challenge this level!\n' \
                          f'ID: {webhook["level_id"]}'
            if 'clears' in webhook["type"]:  # 100/1000 clears
                message = f'🎉 Congratulations, {webhook["author"]}\'s level {webhook["level_name"]} has been cleared ' \
                          f'{webhook["type"].replace("_clears", "")} times, come and play!\n' \
                          f'ID: {webhook["level_id"]}'
    if message != '':
        for chat_id in BOT_ENABLED_CHATS:
            await bot.send_message(
                chat_id=chat_id,
                text=message
            )
        return 'Success'
    else:
        import json
        for chat_id in BOT_ENABLED_CHATS:
            await bot.send_message(
                chat_id=chat_id,
                text=f'{json.dumps(webhook, ensure_ascii=False)}'
            )
        return 'NotImplemented'


def run():
    loop = asyncio.new_event_loop()
    webhook_server = uvicorn.Server(
        config=uvicorn.Config(
            app,
            host=WEBHOOK_HOST,
            port=WEBHOOK_PORT,
            loop="asyncio",
            workers=1
        )
    )
    loop.run_until_complete(webhook_server.serve())


if __name__ == '__main__':
    run()
