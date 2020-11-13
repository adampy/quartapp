from quart import Blueprint, request, current_app
from os import environ
import asyncio
import asyncpg
from hashlib import sha256
from os import urandom
import base64
from functools import wraps
import binascii # Used to catch exceptions when converting from Base64
from datetime import datetime

class HTTPCode:
    '''Enumeration that links HTTP code names to their integer equivalent.'''
    OK = 200
    CREATED = 201
    BADREQUEST = 400
    UNAUTHORIZED = 401
    NOTFOUND = 404

class Auth:
    '''Enumeration that links integers to auth types. This is solely used for abstraction.'''
    NONE = 0
    STUDENT = 1
    TEACHER = 2
    ANY = 3 # Any implies teacher or student authentication is sufficient
    ADMIN = 4 # Implies teacher authentication or admin code needed

def get_auth_details(request):
    '''Utility function that gets the username and password from a request.
Returns `username, password` or False if the request doesn't contain properly formatted Authorization header.'''
    header = request.headers.get('Authorization')
    if not header:
        return False
    try:
        auth = base64.b64decode(header).decode('utf-8')
        username, password = auth.split(':')
        return username, password
    except binascii.Error: # Runs if the Authorization header is Base64 compliant
        return False

def auth_needed(authentication: Auth):
    '''A decorator / wrapper that continues with the wrapped function if correct authentication is given.'''
    def auth(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            details = get_auth_details(request)
            if not details:
                return '', 400 # Improperly formatted Authorization header.
            
            username, password = details # Unpacking tuple
            authenticated = False

            if authentication == Auth.NONE:
                authenticated = True
            elif authentication == Auth.TEACHER:
                authenticated = await is_teacher_valid(username, password)
            elif authentication == Auth.STUDENT:
                authenticated = await is_student_valid(username, password)
            elif authentication == Auth.ANY:
                authenticated = await is_student_valid(username, password) or await is_teacher_valid(username, password)
            elif authentication == Auth.ADMIN:
                admin_code_given = await request.form.data.get("admin")
                authenticated = is_admin_code_valid(admin_code_given) or await is_teacher_valid(username, password)
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
    cache_obj = current_app.config['cache']
    cache = cache_obj.teachers
    if username in cache and cache[username]:
        cache[username][1] = datetime.now()
        return True
    
    # This code block runs if the teacher was not in the cache
    fetched = await current_app.config['db_handler'].fetchrow("SELECT id, password, salt FROM teacher WHERE username = $1", username)
    if not fetched: # If username does not exist
        cache[username] = [False, datetime.now()] # Add username to cache
        cache_obj.update_teacher()
        return False
    
    salt = bytearray.fromhex(fetched[2])
    attempt = await hash_func(password, salt)
    if attempt[1] == fetched[1]:
        cache[username] = [True, datetime.now()] # Add username to cache
        cache_obj.update_teacher()
        return fetched[0] # Teacher is valid
    else:
        cache[username] = [False, datetime.now()] # Add username to cache
        cache_obj.update_teacher()
        return False

async def is_student_valid(username, password):
    '''Checks in the DB if the username + password combination exists. This is a function such that multiple routes can use this function.'''
    cache_obj = current_app.config['cache']
    cache = current_app.config['cache'].students
    if username in cache and cache[username][0]: # Checks the boolean whether the username is valid or not
        cache[username][1] = datetime.now()
        return True
    
    fetched = await current_app.config['db_handler'].fetchrow("SELECT id, password, salt FROM student WHERE username = $1", username)
    if not fetched:
        cache[username] = [False, datetime.now()] # Add username to cache
        cache_obj.update_student()
        return False # No student found with that username
    
    salt = bytearray.fromhex(fetched[2])
    attempt = await hash_func(password, salt)
    if attempt[1] == fetched[1]:
        cache[username] = [True, datetime.now()] # Add username, and ID to cache
        cache_obj.update_student()
        return True # Student is valid
    else:
        cache[username] = [False, datetime.now()] # Add username to cache
        cache_obj.update_student()
        return False

async def hash_func(raw, salt=None):
    '''Hashes a password, `raw`. A salt can be provided or if not its automatically created.'''
    if not salt:
        while True:
            salt = urandom(16) # Generate a 16 byte salt - this means a length of 32 when converted into hex
            taken = await current_app.config['db_handler'].fetchval("""
SELECT EXISTS (SELECT * FROM (SELECT salt FROM student UNION SELECT salt FROM teacher) AS U WHERE U.salt = $1);""", salt.hex()) # Ensures the salt is unique
            if not taken:
                break

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
