from quart import Blueprint, request, current_app
from os import environ
import asyncio
import asyncpg
from hashlib import sha256
from os import urandom
import base64
from functools import wraps
import binascii # Used to catch exceptions when converting from Base64

class HTTPCode:
    '''Enumeration that links HTTP code names to their integer equivalent.'''
    OK = 200
    CREATED = 201
    BADREQUEST = 400
    UNAUTHORIZED = 401
    NOTFOUND = 404

class AuthType:
    '''Enumeration that links integers to auth types. This is solely used for abstraction.'''
    NONE = 0
    STUDENT = 1
    TEACHER = 2
    ANY = 3 # Any implies teacher or student authentication is sufficient

def get_auth_details(request):
    '''Utility function that gets the username and password from a request. Returns `username, password`.'''
    header = request.headers.get('Authorization')
    if not header:
        return False

    try:
        auth = base64.b64decode(header).decode('utf-8')
        username, password = auth.split(':')
        return username, password
    
    except binascii.Error: # Runs if the Authorization header is Base64 compliant
        return False

def auth_needed(authentication: AuthType):
    '''A decorator / wrapper that continues with the wrapped function if correct authentication is given.'''
    def auth(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            details = get_auth_details(request)
            if not details:
                return '', 400
            
            username, password = details # Unpacking tuple
            authenticated = False

            if authentication == AuthType.NONE:
                authenticated = True
            elif authentication == AuthType.TEACHER:
                authenticated = await is_teacher_valid(username, password)
            elif authentication == AuthType.STUDENT:
                authenticated = await is_student_valid(username, password)
            elif authentication == AuthType.ANY:
                authenticated = await is_student_valid(username, password) or await is_teacher_valid(username, password)
            else:
                raise ValueError("`authentication` is a neccessary argument") # Code to prevent me from forgetting the authentication argument

            if authenticated:
                return await f(*args, **kwargs)
            else:
                return '', HTTPCode.UNAUTHORIZED
            
            
            
        return decorated_function
    return auth

async def is_teacher_valid(username, password):
    '''Checks in the DB if the username + password combination exists. This is a function such that multiple routes can use this function.'''
    fetched = await current_app.config['db_handler'].fetchrow("SELECT id, password, salt FROM teacher WHERE username = $1", username)
    if not fetched:
        return False # No teacher found with that username
    salt = bytearray.fromhex(fetched[2])
    if hash_func(password, salt)[1] == fetched[1]:
        return fetched[0] # Returns the ID if a student is valid
    else:
        return False

async def is_student_valid(username, password):
    '''Checks in the DB if the username + password combination exists. This is a function such that multiple routes can use this function.'''
    fetched = await current_app.config['db_handler'].fetchrow("SELECT id, password, salt FROM student WHERE username = $1", username)
    if not fetched:
        return False # No student found with that username
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

def stringify(data):
    '''Wraps a 2D list of records, data, into <pre> tags ready for it to be displayed via HTML.'''
    to_return = "<pre>"
    for record in data:
        to_return += ', '.join([str(x) for x in record])
        to_return += '\n'
    return to_return + "</pre>"

def constant_time_string_check(given, actual):
    '''A constant time string check that prevents timing attacks.'''
    result = False
    for i in range(len(given)):
        try:
            result = given[i] == actual[i]
        except IndexError: # Handling the exception that actual[i] does not exist <=> len(given) > len(actual)
            pass
    return result
        
def is_admin_code_valid(code):
    '''Layer of abstraction to the admin code checking process'''
    return constant_time_string_check(code, environ.get("ADMIN"))

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