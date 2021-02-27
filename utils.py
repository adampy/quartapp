from os import environ
import asyncio
import asyncpg
import datetime
from datetime import datetime
from exceptions import DateTimeParserError

class HTTPCode:
    """Enumeration that links HTTP code names to their integer equivalent."""
    OK = 200
    CREATED = 201
    BADREQUEST = 400
    UNAUTHORIZED = 401
    NOTFOUND = 404

def stringify(data):
    """Wraps a 2D list of records, `data`, into JSON."""
    to_return = '{"data":['
    i = len(data)
    for record in data:
        i -= 1
        if (type(record) == bool):
            to_return += str(record).lower() # Fixes /student/username issues when returning a boolean - False needs to turn to false
        else:
            to_return += str(record)#', '.join([str(x) for x in record])
        if i != 0:
            to_return += ', ' # This is placed between all elements apart from the last one
    return to_return + "]}"

def constant_time_string_check(given, actual):
    """A constant time string check that prevents timing attacks."""
    result = True
    if len(given) != len(actual): result = False
    for i in range(len(given)):
        try:
            result = (given[i] == actual[i]) and result
        except IndexError: # Handling the exception that actual[i] does not exist <=> len(given) > len(actual)
            result = False
    return result
        
def is_admin_code_valid(code):
    """Layer of abstraction to the admin code checking process."""
    return constant_time_string_check(code, environ.get("ADMIN"))

def parse_datetime(string: str):
    """Takes in a string of the format `dd/mm/yyyy|hh:mm` and returns a datetime object. Assumes that the time given is UTC."""
    if not string: return None
    date, time = string.split("|")
    day, month, year = date.split("/")
    hour, minutes = time.split(":")

    if not (day.isdigit() and month.isdigit() and year.isdigit() and hour.isdigit() and minutes.isdigit()):
        raise DateTimeParserError # If any component is not integer
    else:
        day = int(day)
        month = int(month)
        year = int(year)
        hour = int(hour)
        minutes = int(minutes)

    try:
        obj = datetime.replace(datetime.utcnow(), year, month, day, hour, minutes, 0, 0)
        return obj
    except ValueError:
        # The datetime information provided is out of the range. E.g. the day provided may be 40.
        raise DateTimeParserError

def is_password_sufficient(password):
    """Helper function that takes in a password and returns a bool if it is complex enough to be used, otherwise False."""
    upper, lower, digit, colon = False, False, False, False
    if len(password) < 8:
        return False
    for char in password:
        if char == ":":
            colon = colon or True
        if char.isdigit():
            digit = digit or True
        elif char.upper() == char:
            upper = upper or True
        elif char.lower() == char:
            lower = lower or True
    return not colon and (upper and lower and digit)
