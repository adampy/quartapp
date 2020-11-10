import asyncpg
from os import environ

class DatabaseHandler:
    '''A class that is mainly used to reduce the amount of writing multiple async with statements everytime a DB connection is needed.
Having my own class which uses composition also allows me to be more flexible, and means I can add implementation when necessary.'''
    @classmethod
    async def create(cls, *args):
        self = DatabaseHandler()
        self.pool = await asyncpg.create_pool(environ['DATABASE_URL'] + "?sslmode=require", max_size=20)
        return self

    async def create_student(self, student):
        print(student)
        
    async def fetch(self, sql, *params):
        to_return = None
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                to_return = await connection.fetch(sql, *params)
        return (to_return if to_return else [])

    async def fetchrow(self, sql, *params):
        data = await self.fetch(sql, *params)
        return (data[0] if data else [])

    async def execute(self, sql, *params):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(sql, *params)