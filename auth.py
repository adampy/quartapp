from quart import current_app, request
from hashlib import sha256
from os import urandom, environ
import base64
from functools import wraps
import binascii # Used to catch exceptions when converting from Base64
from utils import HTTPCode, is_admin_code_valid

class Auth:
    """Enumeration that links integers to auth types. This is solely used for abstraction."""
    NONE = 0
    STUDENT = 1
    TEACHER = 2
    ANY = 3 # Any implies teacher or student authentication is sufficient
    ADMIN = 4 # Implies teacher authentication or admin code needed

def get_auth_details(request):
    """Utility function that gets the username and password from a request.
Returns `username, password` or False if the request doesn't contain properly formatted Authorization header."""
    header = request.headers.get('Authorization')
    if not header:
        return False
    try:
        auth = base64.b64decode(header).decode('utf-8')
        username, password = auth.split(':')
        return username, password
    except binascii.Error: # Runs if the Authorization header is Base64 compliant
        return False

def auth_needed(authentication: Auth, provide_obj: bool = False):
    """A decorator / wrapper that continues with the wrapped function if correct authentication is given.
    An argument `auth_obj` is passed into the wrapped function if a teacher or student is used to authenticate the route."""
    def auth(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            if authentication == Auth.NONE:
                return await f(*args, **kwargs) # Return the function early such that no errors are raised when checking for user IDs

            student_manager = current_app.config['student_manager']
            teacher_manager = current_app.config['teacher_manager']

            username, password, authenticated = '', '', False
            if authentication != Auth.ADMIN:
                details = get_auth_details(request)
                if not details:
                    return '', HTTPCode.BADREQUEST # Improperly formatted Authorization header.
                else:
                    username, password = details # Unpacking tuple

            if authentication == Auth.TEACHER:
                authenticated = await teacher_manager.is_teacher_valid(username, password)
            elif authentication == Auth.STUDENT:
                authenticated = await student_manager.is_student_valid(username, password)
            elif authentication == Auth.ANY:
                authenticated = await student_manager.is_student_valid(username, password) or await teacher_manager.is_teacher_valid(username, password)
            elif authentication == Auth.ADMIN:
                form = await request.form
                admin = form.get("admin")
                if admin:
                    authenticated = is_admin_code_valid(admin)
                else:
                    authenticated = await teacher_manager.is_teacher_valid(username, password)
            else:
                raise ValueError("`authentication` is a neccessary argument") # Code to prevent me from forgetting the authentication argument

            if authenticated:
                if provide_obj:
                    kwargs['auth_obj'] = authenticated # Passes the ID of the Authorizaiton header into functions key-word arguments. It can be referenced by putting 'auth_id' in function parameters
                return await f(*args, **kwargs)
            else:
                return '', HTTPCode.UNAUTHORIZED
        return decorated_function
    return auth

async def hash_func(raw, salt=None):
    """Hashes a password, `raw`. A salt can be provided or if not its automatically created.
Returns (salt, hashed)"""
    if not salt:
        while True:
            salt = urandom(16) # Generate a 16 byte salt - this means a length of 32 when converted into hex
            taken = await current_app.config['db_handler'].fetchrow("""
SELECT EXISTS (SELECT * FROM (SELECT salt FROM student UNION SELECT salt FROM teacher) AS U WHERE U.salt = $1);""", salt.hex()) # Ensures the salt is unique
            if taken.get("exists") == False:
                break

    password = bytes(raw, 'utf-8') # Convert password to bytes
    to_hash = bytearray(password + salt) # Salt has been appended to the password
    hashed = sha256(to_hash).hexdigest() # Apply the hash
    return salt.hex(), hashed