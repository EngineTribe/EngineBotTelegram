# Engine Tribe API wrapper

from aiohttp import request
from config import *
from models import (
    ServerStats
)


async def user_register(
        username: str,
        im_id: int,
        password_hash: str,
):
    async with request(
            method='POST',
            url=API_HOST + '/user/register',
            data={
                'username': username,
                'password_hash': password_hash,
                'im_id': im_id,
                'api_key': API_KEY
            },
            headers={
                'User-Agent': 'EngineBot'
            }
    ) as response:
        return await response.json()


async def update_password(
        user_identifier: str | int,
        password_hash: str,
        im_id: int,
):
    async with request(
            method='POST',
            url=API_HOST + f'/user/{user_identifier}/update_password',
            data={
                'password_hash': password_hash,
                'api_key': API_KEY,
                'im_id': im_id
            },
            headers={
                'User-Agent': 'EngineBot'
            }
    ) as response:
        return await response.json()


async def user_info(
        user_identifier: str | int
):
    async with request(
            method='POST',
            url=API_HOST + f'/user/{user_identifier}/info',
            headers={
                'User-Agent': 'EngineBot'
            }
    ) as response:
        return await response.json()


async def login_session(
        token: str
) -> str:
    async with request(
            method='POST',
            url=API_HOST + '/user/login',
            data={
                'token': token,
                'alias': 'EngineBot',
                'password': '0'
            },
            headers={
                'User-Agent': 'EngineBot'
            }
    ) as response:
        return (await response.json())['auth_code']


async def get_user_levels(
        username: str,
        auth_code: str,
        rows_perpage: int = 10
) -> list[dict[str, str]]:
    async with request(
            method='POST',
            url=API_HOST + '/stages/detailed_search',
            data={
                'auth_code': auth_code,
                'rows_perpage': rows_perpage,
                'author': username
            },
            headers={
                'User-Agent': 'EngineBot'
            }
    ) as response:
        response_json = await response.json()
        return response_json['result'] if 'result' in response_json else []


async def server_stats() -> ServerStats:
    async with request(
            method='GET',
            url=API_HOST + '/server_stats',
            headers={
                'User-Agent': 'EngineBot'
            }
    ) as response:
        return ServerStats.parse_obj(await response.json())


async def update_permission(
        user_identifier: str,
        permission: str,
        value: bool
):
    async with request(
            method='POST',
            url=API_HOST + f'/user/{user_identifier}/permission/{permission}',
            data={
                'api_key': API_KEY,
                'value': value
            },
            headers={
                'User-Agent': 'EngineBot'
            }
    ) as response:
        return await response.json()


async def random_level(
        auth_code: str,
        difficulty: str | None = None
):
    data = {'dificultad': difficulty, 'auth_code': auth_code} if difficulty is not None else {'auth_code': auth_code}
    async with request(
            method='POST',
            url=API_HOST + '/stage/random',
            data=data,
            headers={
                'User-Agent': 'EngineBot'
            }
    ) as response:
        return (await response.json())


async def query_level(
        auth_code: str,
        level_id: str
):
    async with request(
            method='POST',
            url=API_HOST + f'/stage/{level_id}',
            data={
                'auth_code': auth_code
            },
            headers={
                'User-Agent': 'EngineBot'
            }
    ) as response:
        return (await response.json())
