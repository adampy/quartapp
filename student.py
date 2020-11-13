from quart import Blueprint, request, current_app
import asyncpg
from utils import hash_func, is_student_valid, stringify, auth_needed, get_auth_details # Functions
from utils import HTTPCode, Auth # Enumeratons

bp = Blueprint("student", __name__, url_prefix = "/student")

@bp.route('/auth', methods=['POST'])
@auth_needed(Auth.NONE)
async def auth():
    '''The route that the client uses to verify credentials.'''
    data = await request.form
    username, password = data['username'], data['password']
    if await is_student_valid(username, password):
        return '', HTTPCode.OK
    else:
        return '', HTTPCode.UNAUTHORIZED

@bp.route('/', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_students():
    '''/student route.'''
    db = current_app.config['db_handler'] 
    data = await db.fetch("SELECT * FROM student ORDER BY id;")
    if not data:
        return '', HTTPCode.NOTFOUND
    return stringify(data), HTTPCode.OK

@bp.route('/', methods = ['POST'])
@auth_needed(Auth.TEACHER)
async def new_student():
    db = current_app.config['db_handler']
    data = await request.form
    params = [data['forename'], data['surname'], data['username'], int(data['alps'])]
        
    if data.get('password'):
        salt, hashed = await hash_func(data['password']) # Function that hashes a password
        params.append(hashed)
        params.append(salt)
    else: # Following code run if password not given, set password fields to NULL
        params.append(None)
        params.append(None)

    await db.execute("INSERT INTO student (forename, surname, username, alps, password, salt) VALUES ($1, $2, $3, $4, $5, $6)", *params)
    student_obj = await db.fetchrow("SELECT * FROM student WHERE username = $1", data['username'])
    return stringify([student_obj]), HTTPCode.CREATED

@bp.route('/<param>', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_student(param):
    '''GET STUDENT'''
    username = request.args.get("username")
    db = current_app.config['db_handler']
    sql = ""
    if username:
        sql = "SELECT * FROM student WHERE username = $1"
    else:
        sql = "SELECT * FROM student WHERE id = $1"
        param = int(param) # Change from string to integer if an ID is given

    current_student = await db.fetchrow(sql, param)
    if current_student:
        return stringify([current_student]), HTTPCode.OK
    else:
        return '', HTTPCode.NOTFOUND

@bp.route('/<id>', methods = ['PUT'])
@auth_needed(Auth.TEACHER)
async def put_student(id):
    '''PUT STUDENT'''
    form = await request.form
    id = int(id)

    # Replace student with given object
    username = form.get('username')
    forename = form.get('forename')
    surname = form.get('surname')
    alps = int(form.get('alps'))
    await current_app.config['db_handler'].execute("UPDATE student SET username = $1, forename = $2, surname = $3, alps = $4 WHERE id = $5", username, forename, surname, alps, id)
    return '', HTTPCode.OK

@bp.route('/<id>', methods = ['PATCH'])
async def patch_student(id):
    '''PATCH STUDENT'''
    form = await request.form
    id = int(id)
    db = current_app.config['db_handler']

    details = get_auth_detail(request)
    if is_student_valid(details):
        # Student is updating theirselves
        if form.get('password'):
            salt, hashed = await hash_func(form.get('password')) # Password has been given, now update the salt and password fields
            await db.execute("UPDATE student SET salt = $1, password = $2 WHERE id = $3", salt, hashed, id)

        if form.get('username'):
            await db.execute("UPDATE student SET username = $1 WHERE id = $2", form.get('username'), id)

        if form.get('forename'):
            await db.execute("UPDATE student SET forename = $1 WHERE id = $2", form.get('forename'), id)

        if form.get('surname'):
            await db.execute("UPDATE student SET surname = $1 WHERE id = $2", form.get('surname'), id)

    elif is_teacher_valid(details):
        # Teacher is updating student
        if form.get('alps'):
            alps = form.get('alps')
            try:
                if alps.isdigit() and (0 <= int(alps) <= 90):
                    await db.execute("UPDATE student SET alps = $1 WHERE id = $2", int(alps), id)
                else:
                    raise ValueError # Raise ValueError if parameters are not valid
            except ValueError:
                return 'ValueError', HTTPCode.BADREQUEST
        
        if form.get('password'):
            await db.execute("UPDATE student SET salt = $1, password = $2 WHERE id = $3", None, None, id)

    return '', HTTPCode.OK

@bp.route('/<id>', methods = ['DELETE'])
@auth_needed(Auth.TEACHER)
async def delete_student(id):
    '''DELETE STUDENT'''
    id = int(id)
    await current_app.config['db_handler'].execute("DELETE FROM student WHERE id = $1", id)
    return '', HTTPCode.OK

