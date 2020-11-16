from quart import Blueprint, request, current_app
from utils import stringify, is_admin_code_valid # Functions
from utils import HTTPCode
from auth import Auth, auth_needed, hash_func

bp = Blueprint("teacher", __name__, url_prefix = "/teacher")

@bp.route('/auth', methods=['POST'])
@auth_needed(Auth.NONE)
async def auth():
    '''The route that the client uses to log a user in.'''
    teacher_manager = current_app.config['teacher_manager']
    data = await request.form
    username, password = data['username'], data['password']
    if await teacher_manager.is_teacher_valid(username, password):
        return '', HTTPCode.OK
    else:
        return '', HTTPCode.UNAUTHORIZED

@bp.route("/", methods = ["GET"])
@auth_needed(Auth.ANY)
async def get_teachers():
    '''/teacher route'''
    data = await current_app.config['db_handler'].fetch("SELECT * FROM teacher;")
    if not data:
        return '', HTTPCode.NOTFOUND
    return stringify(data), HTTPCode.OK

@bp.route("/", methods = ["POST"])
@auth_needed(Auth.ADMIN) # Pass obj will return the Admin code here
async def create_teacher():
    '''Creates a new teacher.'''
    db = current_app.config['db_handler']

    data = await request.form
    params = [data['forename'], data['surname'], data['username'], data['title']] # Getting data
    salt, hashed = await hash_func(data['password'])
    params.append(salt)
    params.append(hashed)
    await db.execute("INSERT INTO teacher (forename, surname, username, title, salt, password) VALUES ($1, $2, $3, $4, $5, $6)", *params)
            
    teacher_obj = await db.fetchrow("SELECT * FROM teacher WHERE username = $1", data['username'])
    return stringify([teacher_obj]), HTTPCode.CREATED

@bp.route('/<param>', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_teacher(param):
    '''GET teacher'''
    username = request.args.get("username")
    db = current_app.config['db_handler']
    sql = ""
    if username:
        sql = "SELECT * FROM teacher WHERE username = $1"
    else:
        sql = "SELECT * FROM teacher WHERE id = $1"
        param = int(param) # Change from string to integer if an ID is given

    teacher = await db.fetchrow(sql, param)
    if teacher:
        return stringify([teacher]), HTTPCode.OK
    else:
        return '', HTTPCode.NOTFOUND

@bp.route("/<id>", methods = ["PUT"])
@auth_needed(Auth.ADMIN)
async def put_teacher(id):
    '''PUT teacher'''
    data = await request.form
    db = current_app.config['db_handler']
    id = int(id)

    forename = data.get("forename")
    surname = data.get("surname")
    title = data.get("title")
    username = data.get("username")
    await db.execute("UPDATE teacher SET forename = $1, surname = $2, title = $3, username = $4 WHERE id = $5", forename, surname, title, username, id)
    return '', HTTPCode.OK
    
@bp.route("/<id>", methods = ["PATCH"])
@auth_needed(Auth.TEACHER)
async def patch_teacher(id):
    '''PATCH teacher'''
    if data.get('password'):
        salt, hashed = await hash_func(form.get('password')) # Password has been given, now update the salt and password fields
        await db.execute("UPDATE teacher SET salt = $1, password = $2 WHERE id = $3", salt, hashed, id)
        
    if data.get("username"):
        await db.execute("UPDATE teacher SET username = $1 WHERE id = $2", data.get("username"), id)

    if data.get("forename"):
        await db.execute("UPDATE teacher SET forename = $1 WHERE id = $2", data.get("forename"), id)

    if data.get("surname"):
        await db.execute("UPDATE teacher SET surname = $1 WHERE id = $2", data.get("surname"), id)

    if data.get("title"):
        await db.execute("UPDATE teacer SET title = $1 WHERE id = $2")

    return '', HTTPCode.OK
