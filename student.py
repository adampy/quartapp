from quart import Blueprint, request, current_app
from utils import stringify # Functions
from utils import HTTPCode # Enumeratons
from auth import get_auth_details, hash_func, auth_needed, Auth
from managers import Student

bp = Blueprint("student", __name__, url_prefix = "/student")

@bp.route('/auth', methods=['POST'])
@auth_needed(Auth.NONE)
async def auth():
    """The route that the client uses to verify credentials."""
    student_manager = current_app.config['student_manager']
    data = await request.form
    username, password = data['username'], data['password']
    
    if await student_manager.is_student_valid(username, password):
        return '', HTTPCode.OK
    else:
        return '', HTTPCode.UNAUTHORIZED

@bp.route('/password_reset', methods = ['POST'])
@auth_needed(Auth.NONE)
async def password_reset():
    """Route that can only be used if your password has been changed."""
    form = await request.form
    username = form.get("username")
    current_app.config['student_manager'].cache.remove(username)
    student = await current_app.config['db_handler'].fetchrow("SELECT password, salt FROM student WHERE username = $1", username)
    if not student[0] and not student[1]:
        # Password *has* been reset
        new_password = form.get("password")
        salt, hashed = await hash_func(new_password)
        await current_app.config['db_handler'].execute("UPDATE student SET password = $1, salt = $2 WHERE username = $3", hashed, salt, username)
        return '', HTTPCode.OK
    else:
        return '', HTTPCode.UNAUTHORIZED

@bp.route('/', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_students():
    """/student route."""
    students = current_app.config['student_manager']
    data = await students.get()
    if not data:
        return '', HTTPCode.NOTFOUND
    return stringify(data), HTTPCode.OK

@bp.route('/', methods = ['POST'])
@auth_needed(Auth.TEACHER)
async def new_student():
    data = await request.form
    students = current_app.config['student_manager']
    password = data.get('password') or None # If the password isn't given, make a new password
    
    await students.create(data['forename'], data['surname'], data['username'], int(data['alps']), password = password)
    
    student = await students.get(username = data['username'])
    return stringify([student]), HTTPCode.CREATED

@bp.route('/', methods = ['PATCH'])
@auth_needed(Auth.STUDENT, provide_obj = True)
async def patch_student(auth_obj):
    """PATCH STUDENT (Student editing their own account)"""
    form = await request.form
    student_manager = current_app.config['student_manager']
    to_update = auth_obj.make_copy()

    # Student is updating theirselves
    if form.get('username'):
        to_update.username = form.get('username')

    if form.get('forename'):
        to_update.forename = form.get('forename')

    if form.get('surname'):
        to_update.surname = form.get('surname')

    await student_manager.update(auth_obj, to_update, new_password = form.get('password') or '')
    return '', HTTPCode.OK

@bp.route('/<param>', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_student(param):
    """GET STUDENT"""
    students = current_app.config['student_manager']
    username = request.args.get("username")
    current_student = None

    if username:
        current_student = await students.get(username = username)
    else:
        current_student = await students.get(id = int(param))

    if current_student:
        return stringify([current_student]), HTTPCode.OK
    else:
        return '', HTTPCode.NOTFOUND

@bp.route('/<id>', methods = ['PUT'])
@auth_needed(Auth.TEACHER)
async def put_student(id):
    """PUT STUDENT"""
    form = await request.form
    students = current_app.config['student_manager']
    current_student = await students.get(id = int(id))
    to_update = current_student.make_copy() # Make a new student which we can use to change student values for

    # Replace student with given object
    username = form.get('username')
    forename = form.get('forename')
    surname = form.get('surname')
    alps = int(form.get('alps'))
    if not (username and forename and surname and alps):
        return '', HTTPCode.BADREQUEST
    else:
        to_update.username = username
        to_update.forename = forename
        to_update.surname = surname
        to_update.alps = alps

    await students.update(current_student, to_update)
    return '', HTTPCode.OK

@bp.route('/<id>', methods = ['PATCH'])
@auth_needed(Auth.TEACHER)
async def teacher_patch_student(id):
    """PATCH STUDENT"""
    form = await request.form
    students = current_app.config['student_manager']
    student = await students.get(id = int(id))
    original = student.make_copy()

    # GET DATA FROM FORM AND UPDATE STUDENT IF GIVEN
    username = form.get('username') or None
    forename = form.get('forename') or None
    surname = form.get('surname') or None
    alps = form.get('alps') or None

    if username:
        student.username = username
    if forename:
        student.forename = forename
    if surname:
        student.surname = surname
    if alps:
        if not (alps.isdigit() and (0 <= int(alps) <= 90)):
            return 'ValueError', HTTPCode.BADREQUEST
        else:
            student.alps = int(alps)
    
    # UPDATE DB
    if form.get('password'): # If password needs changing
        await students.update(original, student, reset_password = True)
    else:
        await students.update(original, student)
    return '', HTTPCode.OK

@bp.route('/<id>', methods = ['DELETE'])
@auth_needed(Auth.TEACHER)
async def delete_student(id):
    """DELETE STUDENT"""
    id = int(id)
    await current_app.config['student_manager'].delete(id)
    return '', HTTPCode.OK

