from quart import Blueprint, request, current_app
from os import environ
import asyncio
import asyncpg
from hashlib import sha256
from os import urandom

async def is_student_valid(username, password):
    '''Checks in the DB if the username + password combination exists. This is a function such that multiple routes can use this function.'''
    fetched = await current_app.config['db_handler'].fetchrow("SELECT id, password, salt FROM student WHERE username = $1", username)
    salt = bytearray.fromhex(fetched[2])
    if hash_func(password, salt)[1] == fetched[1]:
        return fetched[0] # Returns the ID if a student is valid
    else:
        return False

def hash_func(raw, salt=None):
    '''Hashes a password, `raw`. A salt can be provided or if not its automatically created.'''
    if not salt: salt = urandom(16) # Generate a 16 byte salt - this means a length of 32 when converted into hex
    password = bytes(raw, 'utf-8') # Convert password to bytes
    to_hash = bytearray(password + salt) # Salt has been appended to the password
    hashed = sha256(to_hash).hexdigest() # Apply the hash
    return salt.hex(), hashed

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
        return to_return

    async def fetchrow(self, sql, *params):
        data = await self.fetch(sql, *params)
        return data[0]

    async def execute(self, sql, *params):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(sql, *params)