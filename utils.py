from os import environ
import asyncio
import asyncpg
from datetime import datetime

class HTTPCode:
    '''Enumeration that links HTTP code names to their integer equivalent.'''
    OK = 200
    CREATED = 201
    BADREQUEST = 400
    UNAUTHORIZED = 401
    NOTFOUND = 404

def stringify(data):
    '''Wraps a 2D list of records, data, into <pre> tags ready for it to be displayed via HTML.'''
    to_return = "<pre>"
    for record in data:
        to_return += str(record)#', '.join([str(x) for x in record])
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
