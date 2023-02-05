from pydantic import BaseModel
from typing import Optional


class ServerStats(BaseModel):
    os: str
    python: str
    player_count: int
    level_count: int
    uptime: int
    connection_per_minute: int
