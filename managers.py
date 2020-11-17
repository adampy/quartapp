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
        """Adds an item to the cache."""
        self.c[key] = value
        self.times[key] = datetime.now()
        self.update_cache()

    def remove(self, key):
        """Removes an item from the cache."""
        if self.c.get(key):
            del self.c[key]
            del self.times[key]

    def update_cache(self):
        """Removes the oldest item from the cache."""
        if len(self.c) > self.limit:
            oldest_key = None
            for key in self.c:
                if oldest_key == None or self.times[key] < self.times[oldest_key]: # Refers to the datetime objects
                    oldest_key = key

            del self.c[oldest_key]

    def get(self, key):
        """Gets the value from the cache, returns False if non-existent."""
        out = self.c.get(key)
        if out:
            self.times[key] = datetime.now() # Update last retrieval time
            return out
        return False

class BaseUser:
    def __init__(self, *args, **kwargs):
        self.data = []
    
    def create_from(self): # Abstract method
        pass

    def __str__(self):
        return "[" + ', '.join([str(attr) for attr in self.data]) + "]"

    def __repr__(self):
        return self.__str__()

class Student(BaseUser):
    """This class is just a structure of data, and does not have any methods"""
    @classmethod
    def create_from(self, data: [], *args, **kwargs):
        super().__init__(self)
        self = Student()
        self.data = data
        self.id = data[0]
        self.forename = data[1]
        self.surname = data[2]
        self.username = data[3]
        self.salt = data[4]
        self.password = data[5]
        self.alps = data[6]
        return self

class Teacher(BaseUser):
    """This class is just a structure of data, and does not have any methods"""
    @classmethod
    def create_from(self, data: [], *args, **kwargs):
        super().__init__(self)
        self = Teacher()
        self.data = data
        self.id = data[0]
        self.forename = data[1]
        self.surname = data[2]
        self.username = data[3]
        self.title = data[4]
        self.password = data[5]
        self.salt = data[6]
        return self
    
class BaseUserManager:
    def __init__(self, student, *args, **kwargs):
        self.cache = Cache(16)
        self.db = current_app.config['db_handler']
        self.is_student = student
        self.is_teacher = not student
        self.table_name = {True: 'student', False:'teacher'}[student] # This is not susseptible to attack (no user inputs)
        self.child_obj = {True: Student, False: Teacher}[student]

    async def get(self, id = -1, username = ""):
        """Gets a user by ID or by Username. This method firstly checks the cache before querying the database."""
        if id == -1 and username == "":
            return False # Argument error

        if id != -1:
            # Search by ID
            for key in self.cache.c:
                if self.cache.c[key].id == id:
                    return self.cache.c[key]

            data = await self.db.fetchrow(f"SELECT * FROM {self.table_name} WHERE id = $1", id)
            if not data:
                return False
            else:
                user = child_obj.create_from(data)
                self.cache.add(user.username, user)
                return user

        elif username != "":
            # Search by username
            cached = self.cache.get(username)
            if not cached:
                data = await self.db.fetchrow(f"SELECT * FROM {self.table_name} WHERE username = $1", username)
                user = child_obj.create_from(data)
                self.cache.add(username, user)
                return user
            else:
                return cached

    async def get_all(self, *args, **kwargs):
        """Returns an array of user objects."""
        all = await self.db.fetch(f"SELECT * FROM {self.table_name} ORDER BY id DESC;")
        to_return = []
        for student in all:
            to_return.append(self.child_obj.create_from(student))
        return to_return

    async def delete(self, id, *args, **kwargs):
        """Delete a user object from the database."""
        await self.db.execute(f"DELETE FROM {self.table_name} WHERE id = $1", id)

    async def is_user_valid(self, username, password):
        """Checks in the DB if the username + password combination exists. This is a function such that multiple routes can use this function.
        The function returns the user data object if the provided credentials are valid, else returns False."""

        # CHECK CACHE
        cache_result = self.cache.get(username)
        if cache_result: # Checks whether the user appears in the cache
            salt_in = bytearray.fromhex(cache_result.salt)
            salt, hashed = await hash_func(password, salt_in)
            if hashed == cache_result.password:
                return cache_result # Returns the user obj
            else:
                return False
    
        # ELSE CHECK DB
        fetched = await self.db.fetchrow(f"SELECT * FROM {self.table_name} WHERE username = $1", username)
        if not fetched:
            return False # No user found with that username
    
        # CHECK HASHES
        user = self.child_obj.create_from(fetched)
        salt = bytearray.fromhex(user.salt)
        attempt = await hash_func(password, salt)
        if attempt[1] == user.password:
            self.cache.add(username, user)
            return user # User is valid, return the obj
        else:
            return False

class StudentManager(BaseUserManager):
    def __init__(self, *args, **kwargs):
        super().__init__(True, *args, **kwargs)

    async def create(self, forename, surname, username, alps, password = None):
        """Creates a student in the DB from the data given."""
        salt = None
        if password:
            salt, hashed = await hash_func(password) # Function that hashes a password

        await self.db.execute("INSERT INTO student (forename, surname, username, alps, password, salt) VALUES ($1, $2, $3, $4, $5, $6)", forename, surname, username, alps, password, salt)

    async def update(self, current_student: Student, student: Student, reset_password = False, new_password = ''):
        """Updates a student object."""
        self.cache.remove(current_student.username) # Remove from cache

        if reset_password: # Set password to None
            await self.db.execute("UPDATE student SET forename = $1, surname = $2, username = $3, alps = $4, password = $5, salt = $6 WHERE id = $7", student.forename, student.surname, student.username, student.alps, None, None, student.id)
        else:
            if new_password == '': # Not resetting password
                await self.db.execute("UPDATE student SET forename = $1, surname = $2, username = $3, alps = $4 WHERE id = $5", student.forename, student.surname, student.username, student.alps, student.id)
            else: # Change password
                salt, hashed = await hash_func(new_password) # Function that hashes a password
                await self.db.execute("UPDATE student SET forename = $1, surname = $2, username = $3, alps = $4, password = $5, salt = $6 WHERE id = $7", student.forename, student.surname, student.username, student.alps, hashed, salt, student.id)

    async def is_student_valid(self, username, password):
        return await self.is_user_valid(username, password)

class TeacherManager(BaseUserManager):
    def __init__(self, *args, **kwargs):
        super().__init__(False, *args, **kwargs)

    async def is_teacher_valid(self, username, password):
        return await self.is_user_valid(username, password)