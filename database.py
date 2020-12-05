import asyncpg
from os import environ
from datetime import datetime

class DatabaseHandler:
    """A class that is mainly used to reduce the amount of writing multiple async with statements everytime a DB connection is needed.
Having my own class which uses composition also allows me to be more flexible, and means I can add implementation when necessary."""

    @classmethod
    async def create(cls, *args):
        """Database creation method. This method can be called from non-async code and it allows async code to be executed."""
        self = DatabaseHandler()
        self.pool = await asyncpg.create_pool(environ['DATABASE_URL'] + "?sslmode=require", max_size=20)
        return self

    async def fetch(self, sql, *params):
        """Database method which executes a command, `sql`, and parameters, `params`, and returns the output.
        Returns the sql output or [] if the command returns nothing."""
        to_return = None
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                to_return = await connection.fetch(sql, *params)
        return (to_return if to_return else [])

    async def fetchrow(self, sql, *params):
        """Database method which executes `sql` with given `params` and returns the first element of the data returned."""
        data = await self.fetch(sql, *params)
        return (data[0] if data else [])

    async def execute(self, sql, *params):
        """Database method which executes an sql command, `sql` with given parameters, `params`.
        `params` are given as multiple arguments."""
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(sql, *params)
