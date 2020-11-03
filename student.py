from quart import Blueprint, request, current_app
import asyncpg
from utils import hash_func, is_student_valid

bp = Blueprint("student", __name__, url_prefix = "/student")

def stringify(data):
    '''Wraps a 2D list of records, data, into <pre> tags ready for it to be displayed via HTML'''
    to_return = "<pre>"
    for record in data:
        to_return += ', '.join([str(x) for x in record])
        to_return += '\n'
    return to_return + "</pre>"

@bp.route('/auth', methods=['POST'])
async def auth():
    '''The route that the client uses to log a user in.'''
    data = await request.form
    username, password = data['username'], data['password']
    results = await is_student_valid(username, password)
    if results:
        return str(results), 200
    else:
        return '', 401

@bp.route('/', methods = ['GET', 'POST'])
async def get_students():
    '''/student route.'''
    db = current_app.config['db_handler']

    if request.method == 'GET': # Get all students
        data = await db.fetch("SELECT * FROM student ORDER BY id;")
        return stringify(data)

    elif request.method == 'POST': # Create a new student
        data = await request.form
        params = [data['forename'], data['surname'], data['username'], int(data['alps'])]
        
        if data.get('password'):
            salt, hashed = hash_func(data['password']) # Function that hashes a password
            params.append(hashed)
            params.append(salt)
        else: # Following code run if password not given, set password fields to NULL
            params.append(None)
            params.append(None)

        await db.execute("INSERT INTO student (forename, surname, username, alps, password, salt) VALUES ($1, $2, $3, $4, $5, $6)", *params)
        student_obj = await db.fetchrow("SELECT * FROM student WHERE username = $1", data['username'])
        return stringify([student_obj]), 201
        

@bp.route('/<id>', methods = ['GET', 'PUT', 'PATCH', 'DELETE'])
async def student_function(id):
    db = current_app.config['db_handler']
    form = await request.form
    id = int(id)

    current_student = await db.fetchrow("SELECT * FROM student WHERE id = $1", id)

    if request.method == 'GET':
        # Get given student
        return stringify([current_student]), 200
    
    elif request.method == 'PUT':
        # Replace student with given object
        username = form.get('username')
        forename = form.get('forename')
        surname = form.get('surname')
        alps = int(form.get('alps'))
        await db.execute("UPDATE student SET username = $1, forename = $2, surname = $3, alps = $4", username, forename, surname, alps)
    
    elif request.method == 'PATCH':
        # Update given student
        if form.get('password'):
            salt, hashed = hash_func(form.get('password')) # Password has been given, now update the salt and password fields
            await db.execute("UPDATE student SET salt = $1, password = $2 WHERE id = $3", salt, hashed, id)
        
        if form.get('alps'):
            alps = form.get('alps')
            try:
                if alps.isdigit() and (0 <= int(alps) <= 90):
                    await db.execute("UPDATE student SET alps = $1 WHERE id = $2", int(alps), id)
                else:
                    raise ValueError # Raise ValueError if parameters are not valid
            except ValueError:
                return 'ValueError', 400 # Return HTTP 400 Bad Request

        if form.get('username'):
            await db.execute("UPDATE student SET username = $1 WHERE id = $2", form.get('username'), id)

        if form.get('forename'):
            await db.execute("UPDATE student SET forename = $1 WHERE id = $2", form.get('forename'), id)

        if form.get('surname'):
            await db.execute("UPDATE student SET surname = $1 WHERE id = $2", form.get('surname'), id)

        return '', 200
    
    elif reqeust.method == 'DELETE':
        # Delete given student
        await db.execute("DELETE FROM student WHERE id = $1", id)
        return '', 200
    
@bp.route('/error', methods = ['GET'])
async def error():
    return '', 401
