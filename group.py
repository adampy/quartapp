from quart import Blueprint, request, current_app
from utils import stringify, parse_datetime # Functions
from utils import HTTPCode # Enumeratons
from auth import auth_needed, Auth
from datetime import datetime, timedelta # For making a task and setting deadline
from objects import Student

bp = Blueprint("group", __name__, url_prefix = "/group")

@bp.route('/', methods = ['GET'])
@auth_needed(Auth.ANY, provide_obj = True)
async def get_groups(auth_obj):
    """Subroutine that gets all the groups. A student only has access to their groups, and a teacher can request all groups (be default) or their own by setting ?mine=True"""
    groups = current_app.config['group_manager']

    if type(auth_obj) == Student:
        data = await groups.get(student_id = auth_obj.id)
    else:
        get_all_groups = request.args.get("mine") != "True"
        if get_all_groups:
            data = await groups.get()
        else:
            data = await groups.get(teacher_id = auth_obj.id)

    if not data:
        return '', HTTPCode.NOTFOUND

    return stringify(data), HTTPCode.OK

@bp.route('/<id>', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_group(id):
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    groups = current_app.config['group_manager']
    data = await groups.get(group_id = int(id))
    if not data:
        return '', HTTPCode.NOTFOUND
    return stringify([data]), HTTPCode.OK

@bp.route('/', methods = ['POST'])
@auth_needed(Auth.TEACHER, provide_obj=True)
async def make_group(auth_obj):
    """Subroutine that makes a new group. The teacher that accesses this route automatically becomes the teacher of the group.
    This can be changed by doing a PATCH request afterwards."""
    data = await request.form
    name = data.get('name')
    subject = data.get('subject')

    if not (name and subject):
        return '', HTTPCode.BADREQUEST # Not all necessary arguments given

    groups = current_app.config['group_manager']
    await groups.create(auth_obj.id, name, subject)
    teachers_groups = await groups.get(teacher_id = auth_obj.id)
    new_group = max(teachers_groups, key = lambda x: x.id)
    return '', HTTPCode.CREATED, {"Location":bp.url_prefix + "/" + str(new_group.id)}

@bp.route('/<id>', methods = ['DELETE'])
@auth_needed(Auth.TEACHER)
async def delete_group(id):
    """Top level subroutine that deletes a group given by `id`."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    groups = current_app.config['group_manager']
    await groups.delete(int(id)) # We know that the int must be integer at this point
    return '', HTTPCode.OK

@bp.route('/<id>', methods = ['PUT'])
@auth_needed(Auth.TEACHER)
async def put_group(id):
    """The route that updates a group, `id`, to newly given data, given in the form data of the request."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST
    
    data = await request.form
    teacher_id = data.get("teacher_id") or None
    subject = data.get("subject") or None
    name = data.get("name") or None

    if not (teacher_id and teacher_id.isdigit() and subject and name):
        return '', HTTPCode.BADREQUEST # Some necessary arguments are missing, return 400

    groups = current_app.config['group_manager']
    to_update = await groups.get(group_id= int(id))
    if not to_update:
        return '', HTTPCode.NOTFOUND
    to_update.teacher_id = int(teacher_id)
    to_update.subject = subject
    to_update.name = name
    
    try:
        await groups.update(to_update)
        return '', HTTPCode.OK
    except Exception as e: # The only exception that may arise is a FK constraint error on teacher_id
        return '', HTTPCode.BADREQUEST

@bp.route('/<id>', methods = ['PATCH'])
@auth_needed(Auth.TEACHER)
async def patch_group(id):
    """Top level subroutine that edits one or more fields on a group."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST
    
    data = await request.form
    groups = current_app.config['group_manager']
    current = await groups.get(group_id = int(id))
    if not current:
        return '', HTTPCode.NOTFOUND

    name = data.get("name") or None
    subject = data.get("subject") or None
    teacher_id = data.get("teacher_id") or None

    if teacher_id and not teacher_id.isdigit(): # Only check if there is a ID provided
        return '', HTTPCode.BADREQUEST

    if name:
        current.name = name
    if subject:
        current.subject = subject
    if teacher_id:
        current.teacher_id = int(teacher_id)
    
    await groups.update(current)
    return '', HTTPCode.OK

@bp.route('/<id>/join', methods = ['POST'])
@auth_needed(Auth.TEACHER)
async def join_group(id):
    """Route that adds students to the group. Student IDs are provided in the form data under `students` key."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    data = await request.form
    raw_students = data.get("students") or None
    if not raw_students:
        return '', HTTPCode.BADREQUEST

    students = [int(id) for id in raw_students.split(',') if id.isdigit()]
    groups = current_app.config['group_manager']
    for student_id in students:
        await groups.add_student(student_id, int(id))
    return '', HTTPCode.OK

@bp.route('/<id>/leave', methods = ['POST'])
@auth_needed(Auth.TEACHER)
async def leave_group(id):
    """Route that removes students from a group."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    data = await request.form
    raw_students = data.get("students") or None
    if not raw_students:
        return '', HTTPCode.BADREQUEST

    students = [int(id) for id in raw_students.split(',') if id.isdigit()]
    groups = current_app.config['group_manager']
    for student_id in students:
        await groups.remove_student(student_id, int(id))
    return '', HTTPCode.OK

@bp.route('/<id>/students', methods = ['GET'])
@auth_needed(Auth.TEACHER)
async def get_group_students(id):
    """Get all the students in a given group."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST
    
    groups = current_app.config['group_manager']
    data = await groups.students(int(id))
    return stringify(data), HTTPCode.OK

# -- TASKS --

@bp.route('/<id>/task', methods = ['POST'])
@auth_needed(Auth.TEACHER)
async def make_new_task(id):
    """Route that creates a new task for a given group. When providing the date due, it must be in UTC, and the format: dd/mm/yyyy|hh:mm"""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    data = await request.form
    title = data.get("title") or None
    description = data.get("description") or None
    max_score = data.get("max_score") or None
    to_parse = data.get("date_due") or None

    date_due = parse_datetime(to_parse)

    if not title or not description or not max_score or not max_score.isdigit() or not date_due:
        return '', HTTPCode.BADREQUEST # Not all necessary args given, return BADREQUEST

    tasks = current_app.config['task_manager']
    await tasks.create(int(id), title, description, date_due, int(max_score))
    all_tasks = await tasks.get(group_id = int(id))
    new_task = max(all_tasks, key = lambda x: x.id)
    return '', HTTPCode.CREATED, {"Location": "/task/" + str(new_task.id)}

@bp.route('/<id>/task', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_group_tasks(id):
    """Route that gets all the tasks relating to a group. Any authentication level needed."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    tasks = current_app.config['task_manager']
    data = await tasks.get(group_id = int(id))
    if not data:
        return '', HTTPCode.NOTFOUND
    else:
        return stringify(data), HTTPCode.OK