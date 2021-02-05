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

class AbstractBaseObject:
    def __init__(self, *args, **kwargs):
        self.data = []
    
    def create_from(self): # Abstract method
        pass

    def __str__(self):
        """Gives the JSON representation of the object."""
        string = "{"
        attrs = [x for x in dir(self) if (not x.startswith("__") and not x.endswith("__") and x not in ["make_copy", "create_from", "data", "password", "salt"])] # This line gets all attributes of the object, not including methods, `data`, `password`, and `salt`
        i = len(attrs) # Counter used to see if the element being added is the last one (if so it doesn't need a ",")
        for attr in attrs:
            i -= 1
            val = getattr(self, attr)
            if val == None:
                string += f'"{attr}": null'
            elif type(val) == str or type(val) == datetime:
                # If string, place inside ""
                string += f'"{attr}": "{val}"'
            elif type(val) == bool:
                string += f'"{attr}": {"true" if val else "false"}'
            else:
                # Check here for any IDs that need a "ref" object
                if (attr.endswith("_id")):
                    obj_name = attr.split("_id")[0]
                    string += '"' + obj_name + '": {"reference": {"id": ' + str(val) + ', "link": "/' + obj_name + '/' + str(val) + '"}}' # Gives JSON ref object
                else:
                    string += f'"{attr}": {str(val)}'

            if i != 0: # If not the last element in attrs
                string += ", "#\n"

        string += "}"
        return string
        
        #return "[" + ', '.join([str(attr) for attr in self.data]) + "]" Old __str__ method

    def __repr__(self):
        return self.__str__()

    def make_copy(self):
        '''Function that returns itself, but as a new copy'''
        return self.create_from(self.data[:])

class Student(AbstractBaseObject):
    """This class is just a structure of data, and does not have any methods"""
    @classmethod
    def create_from(cls, data: [], *args, **kwargs):
        """Data supplied must follow [id, forename, surname, username, salt, password, alps]."""
        super().__init__(cls)
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

class Teacher(AbstractBaseObject):
    """This class is just a structure of data, and does not have any methods"""
    @classmethod
    def create_from(cls, data: [], *args, **kwargs):
        """Data supplied must follow: [id, forename, surname, username, title, password, salt]."""
        super().__init__(cls)
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
    
class Group(AbstractBaseObject):
    @classmethod
    def create_from(cls, data: [], *args, **kwargs):
        """Data supplied must follow: [id, teacher_id, name, subject]"""
        super().__init__(cls)
        self = Group()
        self.data = data
        self.id = data[0]
        self.teacher_id = data[1]
        self.name = data[2]
        self.subject = data[3]
        return self

class Task(AbstractBaseObject):
    @classmethod
    def create_from(cls, data: [], *args, **kwargs):
        """Data supplied must follow: [id, group_id, description, date_set, date_due, max_score, has_completed = False]"""
        super().__init__(cls)
        self = Task()
        self.data = data
        self.id = data[0]
        self.group_id = data[1]
        self.title = data[2]
        self.description = data[3]
        self.date_set = data[4]
        self.date_due = data[5]
        self.max_score = data[6]
        try:
            self.has_completed = data[7]
        except IndexError:
            pass

        return self

class Mark(AbstractBaseObject):
    @classmethod
    def create_from(cls, data: [], *args, **kwargs):
        """Data supplied must follow: [student_id, task_id, has_completed, has_marked, score, feedback]"""
        super().__init__(cls)
        self = Task()
        self.data = data
        self.student_id = data[0]
        self.task_id = data[1]
        self.has_completed = data[2]
        self.has_marked = data[3]
        self.score = data[4]
        self.feedback = data[5]

        return self
