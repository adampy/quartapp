from quart import current_app
from auth import hash_func, Auth
from utils import HTTPCode
from datetime import datetime

class Cache:
    def __init__(self, limit, *args, **kwargs):
        self.c = {}
        self.times = {}
        self.limit = limit

    def add(self, key, value):
        '''Adds an item to the cache.'''
        self.c[key] = value
        self.times[key] = datetime.now()
        self.update_cache()

    def remove(self, key):
        '''Removes an item from the cache.'''
        if self.c.get(key):
            del self.c[key]
            del self.times[key]

    def update_cache(self):
        '''Removes the oldest item from the cache.'''
        if len(self.c) > self.limit:
            oldest_key = None
            for key in self.c:
                if oldest_key == None or self.times[key] < self.times[oldest_key]: # Refers to the datetime objects
                    oldest_key = key

            del self.c[oldest_key]

    def get(self, key):
        '''Gets the value from the cache, returns False if non-existent.'''
        out = self.c.get(key)
        if out:
            self.times[key] = datetime.now() # Update last retrieval time
            return out
        return False

class Student:
    '''This class is just a structure of data, and does not have any methods'''
    @classmethod
    def create_from(self, data: [], *args, **kwargs):
        self = Student()
        self.id = data[0]
        self.forename = data[1]
        self.surname = data[2]
        self.username = data[3]
        self.salt = data[4]
        self.password = data[5]
        self.alps = data[6]
        return self

    def __str__(self):
        return "[" + ', '.join([str(self.id), self.forename, self.surname, self.username, str(self.salt), str(self.password), str(self.alps)]) + "]"

    def __repr__(self):
        return self.__str__()

class StudentManager:
    def __init__(self, *args, **kwargs):
        self.cache = Cache(16)
        self.db = current_app.config['db_handler']

    async def is_student_valid(self, username, password):
        '''Checks in the DB if the username + password combination exists. This is a function such that multiple routes can use this function.
        The function returns the student data object if the provided credentials are valid, else returns False.'''

        # CHECK CACHE
        cache_result = self.cache.get(username)
        if cache_result: # Checks whether the student appears in the cache
            salt_in = bytearray.fromhex(cache_result.salt)
            salt, hashed = await hash_func(password, salt_in)
            if hashed == cache_result.password:
                return cache_result # Returns the student obj
            else:
                return False
    
        # ELSE CHECK DB
        fetched = await self.db.fetchrow("SELECT * FROM student WHERE username = $1", username)
        if not fetched:
            return False # No student found with that username
    
        # CHECK HASHES
        student = Student.create_from(fetched)
        salt = bytearray.fromhex(student.salt)
        attempt = await hash_func(password, salt)
        if attempt[1] == student.password:
            self.cache.add(username, student)
            return student # Student is valid, return the obj
        else:
            return False

    async def get(self, id = -1, username = ""):
        '''Gets a student by ID or by Username. This method firstly checks the cache before querying the database.'''
        if id == -1 and username == "":
            return False # Argument error

        if id != -1:
            # Search by ID
            for key in self.cache.c:
                if self.cache.c[key].id == id:
                    return self.cache.c[key]

            data = await self.db.fetchrow("SELECT * FROM student WHERE id = $1", id)
            if not data:
                return False
            else:
                student_obj = Student.create_from(data)
                self.cache.add(student_obj.username, student_obj)
                return student_obj

        elif username != "":
            # Search by username
            cached = self.cache.get(username)
            if not cached:
                data = await self.db.fetchrow("SELECT * FROM student WHERE username = $1", username)
                student_obj = Student.create_from(data)
                self.cache.add(username, student_obj)
                return student_obj
            else:
                return cached

    async def get_all(self):
        '''Returns an array of student objects.'''
        all = await self.db.fetch("SELECT * FROM student ORDER BY id DESC;")
        to_return = []
        for student in all:
            to_return.append(Student.create_from(student))
        return to_return

    async def create(self, forename, surname, username, alps, password = None):
        '''Creates a student in the DB from the data given.'''
        salt = None
        if password:
            salt, hashed = await hash_func(password) # Function that hashes a password

        await self.db.execute("INSERT INTO student (forename, surname, username, alps, password, salt) VALUES ($1, $2, $3, $4, $5, $6)", forename, surname, username, alps, password, salt)

    async def delete(self, id):
        '''Delete a student.'''
        await self.db.execute("DELETE FROM student WHERE id = $1", id)

    async def update(self, current_student: Student, student: Student, reset_password = False, new_password = ''):
        '''Updates a student object.'''
        self.cache.remove(current_student.username) # Remove from cache

        if reset_password: # Set password to None
            await self.db.execute("UPDATE student SET forename = $1, surname = $2, username = $3, alps = $4, password = $5, salt = $6 WHERE id = $7", student.forename, student.surname, student.username, student.alps, None, None, student.id)
        else:
            if new_password == '': # Not resetting password
                await self.db.execute("UPDATE student SET forename = $1, surname = $2, username = $3, alps = $4 WHERE id = $5", student.forename, student.surname, student.username, student.alps, student.id)
            else: # Change password
                salt, hashed = await hash_func(new_password) # Function that hashes a password
                await self.db.execute("UPDATE student SET forename = $1, surname = $2, username = $3, alps = $4, password = $5, salt = $6 WHERE id = $7", student.forename, student.surname, student.username, student.alps, hashed, salt, student.id)


class Teacher:
    '''This class is just a structure of data, and does not have any methods'''
    @classmethod
    def create_from(self, data: [], *args, **kwargs):
        self = Teacher()
        self.id = data[0]
        self.forename = data[1]
        self.surname = data[2]
        self.username = data[3]
        self.title = data[4]
        self.password = data[5]
        self.salt = data[6]
        return self

    def __str__(self):
        return "[" + ', '.join([self.id, self.forename, self.surname, self.username, self.title, self.password, self.salt]) + "]"

class TeacherManager:
    def __init__(self, *args, **kwargs):
        self.cache = Cache(16)
        self.db = current_app.config['db_handler']

    async def is_teacher_valid(self, username, password):
        '''Checks in the DB if the username + password combination exists. This is a function such that multiple routes can use this function.
        The function returns the teacher ID if the provided credentials are valid, else returns False.'''
        
        # CHECK CACHE
        cache_result = self.cache.get(username)
        if cache_result: # Checks whether the teacher appears in the cache
            return cache_result # Returns the teacher obj
    
        # ELSE CHECK DB
        fetched = await self.db.fetchrow("SELECT * FROM teacher WHERE username = $1", username)
        if not fetched: # If username does not exist
            return False
    
        # CHECK HASHES
        teacher = Teacher.create_from(fetched)
        salt = bytearray.fromhex(teacher.salt)
        attempt = await hash_func(password, salt)
        if attempt[1] == teacher.password:
            self.cache.add(username, teacher) # Add username to cache
            return teacher # Teacher is valid
        else:
            return False