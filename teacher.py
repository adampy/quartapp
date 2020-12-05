from quart import Blueprint, request, current_app
from utils import stringify, is_admin_code_valid # Functions
from utils import HTTPCode
from auth import Auth, auth_needed, hash_func
from exceptions import UsernameTaken

bp = Blueprint("teacher", __name__, url_prefix = "/teacher")

@bp.route('/auth', methods=['POST']) #DONE
@auth_needed(Auth.NONE)
async def auth():
    """The route that the client uses to verify credentials."""
    teacher_manager = current_app.config['teacher_manager']
    data = await request.form
    username, password = data['username'], data['password']

    if await teacher_manager.is_teacher_valid(username, password):
        return '', HTTPCode.OK
    else:
        return '', HTTPCode.UNAUTHORIZED

@bp.route("/", methods = ["GET"]) #DONE
@auth_needed(Auth.ANY)
async def get_teachers():
    """/teacher route"""
    teachers = await current_app.config['teacher_manager'].get()
    if not teachers:
        return '', HTTPCode.NOTFOUND
    return stringify(teachers), HTTPCode.OK

@bp.route("/", methods = ["PATCH"]) #DONE
@auth_needed(Auth.TEACHER, provide_obj = True)
async def patch_own_teacher(auth_obj):
    form = await request.form
    teacher = auth_obj.make_copy()
    teachers = current_app.config['teacher_manager']

    # GET DATA FROM FORM AND UPDATE TEACHER IF GIVEN
    username = form.get('username') or None
    forename = form.get('forename') or None
    surname = form.get('surname') or None
    title = form.get('title') or None

    if username:
        teacher.username = username
    if forename:
        teacher.forename = forename
    if surname:
        teacher.surname = surname
    if title:
        teacher.title = title
    
    # UPDATE DB
    if form.get('password'): # If password needs changing
        await teachers.update(auth_obj, teacher, new_password = form.get('password'))
    else:
        await teachers.update(auth_obj, teacher)
    return '', HTTPCode.OK

@bp.route("/", methods = ["POST"])
@auth_needed(Auth.ADMIN) # (Pass obj will return the Admin code here if done with admin code, else a new teacher)
async def create_teacher():
    """Creates a new teacher."""
    data = await request.form
    teachers = current_app.config['teacher_manager']

    try:
        await teachers.create(data['forename'], data['surname'], data['username'], data['title'], data['password'])
        teacher = await teachers.get(username = data['username'])
        return stringify([teacher]), HTTPCode.CREATED
    except UsernameTaken:
        return '', HTTPCode.BADREQUEST # Username taken

@bp.route('/<param>', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_teacher(param):
    """GET teacher"""
    username = request.args.get("username")
    teachers = current_app.config['teacher_manager']
    teacher = None

    if username:
        teacher = await teachers.get(username = username)
    else:
        id = int(param) # Change from string to integer if an ID is given
        teacher = await teachers.get(id = id)

    if teacher:
        return stringify([teacher]), HTTPCode.OK
    return '', HTTPCode.NOTFOUND

@bp.route("/<id>", methods = ["PUT"]) #DONE
@auth_needed(Auth.ADMIN)
async def put_teacher(id):
    """PUT TEACHER"""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    form = await request.form
    teachers = current_app.config['teacher_manager']
    current_teacher = await teachers.get(id = int(id))
    to_update = current_teacher.make_copy() # Make a new teacher which we can use to change student values for

    # Replace student with given object
    username = form.get('username')
    forename = form.get('forename')
    surname = form.get('surname')
    title = int(form.get('title'))
    if not (username and forename and surname and title):
        return '', HTTPCode.BADREQUEST
    else:
        to_update.username = username
        to_update.forename = forename
        to_update.surname = surname
        to_update.title = title

    await teachers.update(current_teacher, to_update)
    return '', HTTPCode.OK
    
@bp.route("/<id>", methods = ["PATCH"]) #DONE
@auth_needed(Auth.TEACHER)
async def patch_teacher(id):
    """PATCH teacher"""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    form = await request.form
    teachers = current_app.config['teacher_manager']
    teacher = await teachers.get(id = int(id))
    original = teacher.make_copy() # Make a new copy that we can edit

    # GET DATA FROM FORM AND UPDATE TEACHER IF GIVEN
    username = form.get('username') or None
    forename = form.get('forename') or None
    surname = form.get('surname') or None
    title = form.get('title') or None

    if username:
        teacher.username = username
    if forename:
        teacher.forename = forename
    if surname:
        teacher.surname = surname
    if title:
        teacher.title = title
    
    # UPDATE DB
    if form.get('password'): # If password needs changing
        await teachers.update(original, teacher, new_password = form.get('password'))
    else:
        await teachers.update(original, teacher)
    return '', HTTPCode.OK