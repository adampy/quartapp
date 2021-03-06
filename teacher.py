﻿from quart import Blueprint, request, current_app
from utils import stringify, is_admin_code_valid, is_password_sufficient # Functions
from utils import HTTPCode
from auth import Auth, auth_needed, hash_func
from exceptions import UsernameTaken

bp = Blueprint("teacher", __name__, url_prefix = "/teacher")

@bp.route('/auth', methods=['POST'])
@auth_needed(Auth.NONE)
async def auth():
    """The route that the client uses to verify credentials."""
    teacher_manager = current_app.config['teacher_manager']
    data = await request.form
    username = data.get("username")
    password = data.get("password")
    if not (username and password):
        return '', HTTPCode.BADREQUEST

    if await teacher_manager.is_teacher_valid(username, password):
        return '', HTTPCode.OK
    else:
        return '', HTTPCode.UNAUTHORIZED

@bp.route("/username", methods = ["POST"])
@auth_needed(Auth.ADMIN)
async def username_taken():
    """Route that returns true if the username is taken. Requires admin authentication with the admin code."""
    data = await request.form
    username = data.get("username")
    if not username:
        return '', HTTPCode.BADREQUEST
    taken = await current_app.config['teacher_manager'].is_username_taken(username)
    return stringify([taken]), HTTPCode.OK

@bp.route("/", methods = ["GET"])
@auth_needed(Auth.ANY)
async def get_teachers():
    """/teacher route"""
    teachers = await current_app.config['teacher_manager'].get()
    if not teachers:
        return '', HTTPCode.NOTFOUND
    return stringify(teachers), HTTPCode.OK

@bp.route("/", methods = ["PATCH"])
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
        new_password = form.get('password')
        if not is_password_sufficient(new_password):
            return '', HTTPCode.BADREQUEST
        try:
            await teachers.update(auth_obj, teacher, new_password = new_password)
        except UsernameTaken:
            return '', HTTPCode.BADREQUEST
    else:
        try:
            await teachers.update(auth_obj, teacher)
        except UsernameTaken:
            return '', HTTPCode.BADREQUEST
    return '', HTTPCode.OK

@bp.route("/", methods = ["POST"])
@auth_needed(Auth.ADMIN) # (Pass obj will return the Admin code here if done with admin code, else a new teacher)
async def create_teacher():
    """Creates a new teacher."""
    data = await request.form
    teachers = current_app.config['teacher_manager']

    try:
        if not is_password_sufficient(data['password']):
            return '', HTTPCode.BADREQUEST
        forename = data.get("forename")
        surname = data.get("surname")
        username = data.get("username")
        title = data.get("title")
        password = data.get("password")
        if not (forename and surname and title and password):
            return '', HTTPCode.BADREQUEST

        await teachers.create(forename, surname, username if username else "", title, password)
        all_teachers = await teachers.get()
        teacher = max(all_teachers, key = lambda x: x.id) # Returns the newest teacher
        return stringify([teacher]), HTTPCode.CREATED, {"Location":bp.url_prefix + "/" + str(teacher.id)}
    except UsernameTaken:
        return '', HTTPCode.BADREQUEST # Username taken

@bp.route("/<id>", methods = ["DELETE"])
@auth_needed(Auth.ADMIN) # Only admins can delete teachers
async def delete_teacher(id):
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST
    
    await current_app.config['teacher_manager'].delete(int(id))
    return '', HTTPCode.OK

@bp.route('/<param>', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_teacher(param):
    """GET teacher"""
    username = request.args.get("username")
    teachers = current_app.config['teacher_manager']

    if username:
        teacher = await teachers.get(username = param)
    else:
        if not param.isdigit():
            return '', HTTPCode.BADREQUEST
        id = int(param) # Change from string to integer if an ID is given
        teacher = await teachers.get(id = id)

    if teacher:
        return stringify([teacher]), HTTPCode.OK
    return '', HTTPCode.NOTFOUND

@bp.route("/<id>", methods = ["PUT"])
@auth_needed(Auth.ADMIN)
async def put_teacher(id):
    """PUT TEACHER"""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    form = await request.form
    teachers = current_app.config['teacher_manager']
    current_teacher = await teachers.get(id = int(id))
    if not current_teacher:
        return '', HTTPCode.NOTFOUND
    to_update = current_teacher.make_copy() # Make a new teacher which we can use to change student values for

    # Replace student with given object
    username = form.get('username')
    forename = form.get('forename')
    surname = form.get('surname')
    title = form.get('title')
    if not (username and forename and surname and title):
        return '', HTTPCode.BADREQUEST
    else:
        to_update.username = username
        to_update.forename = forename
        to_update.surname = surname
        to_update.title = title

    try:
        await teachers.update(current_teacher, to_update)
    except UsernameTaken:
        return '', HTTPCode.BADREQUEST
    return '', HTTPCode.OK
    
@bp.route("/<id>", methods = ["PATCH"])
@auth_needed(Auth.ADMIN)
async def patch_teacher(id):
    """PATCH teacher"""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    form = await request.form
    teachers = current_app.config['teacher_manager']
    teacher = await teachers.get(id = int(id))
    if not teacher:
        return '', HTTPCode.NOTFOUND
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
        new_password = form.get('password')
        if not is_password_sufficient(new_password):
            return '', HTTPCode.BADREQUEST
        try:
            await teachers.update(original, teacher, new_password = form.get('password'))
        except UsernameTaken:
            return '', HTTPCode.BADREQUEST
    else:
        try:
            await teachers.update(original, teacher)
        except UsernameTaken:
            return '', HTTPCode.BADREQUEST
    return '', HTTPCode.OK