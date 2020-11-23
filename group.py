from quart import Blueprint, request, current_app
from utils import stringify # Functions
from utils import HTTPCode # Enumeratons
from auth import auth_needed, Auth

bp = Blueprint("group", __name__, url_prefix = "/group")

@bp.route('/', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_groups():
    groups = current_app.config['group_manager']
    data = await groups.get()

    if not data:
        return '', HTTPCode.NOTFOUND

    return stringify(data), HTTPCode.OK

@bp.route('/<id>', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_group(id):
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    groups = current_app.config['group_manager']
    data = await groups.get(id = int(id))
    if not data:
        return '', HTTPCode.NOTFOUND
    return stringify([data]), HTTPCode.OK

@bp.route('/', methods = ['POST'])
@auth_needed(Auth.TEACHER, provide_obj=True)
async def make_group(auth_obj):
    """Subroutine that makes a new group. The teacher that accesses this route automatically becomes the teacher of the group.
    This can be changed by doing a PATCH request afterwards."""
    data = await request.form
    name = data.get('name') or None
    subject = data.get('subject') or None

    if not name or not subject:
        return '', HTTPCode.BADREQUEST # Not all necessary arguments given

    groups = current_app.config['group_manager']
    await groups.create(auth_obj.id, data['name'], data['subject'])
    return '', HTTPCode.CREATED

@bp.route('/<id>', methods = ['DELETE'])
@auth_needed(Auth.TEACHER)
async def delete_group(id):
    """Top level subroutine that deletes a group given by `id`."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    groups = current_app.config['group_manager']
    await groups.delete(int(id)) # We know that the int must be integer at this point
    #to_delete = await groups.get(id = int(id))
    #await groups.delete(to_delete)
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

    if not teacher_id or not subject or not name or not teacher_id.isdigit():
        return '', HTTPCode.BADREQUEST # Some necessary arguments are missing, return 400

    groups = current_app.config['group_manager']
    to_update = await groups.get(id= int(id))
    to_update.teacher_id = int(teacher_id)
    to_update.subject = subject
    to_update.name = name
    await groups.update(to_update)
    return '', HTTPCode.OK

@bp.route('/<id>', methods = ['PATCH'])
@auth_needed(Auth.TEACHER)
async def patch_group(id):
    """Top level subroutine that edits one or more fields on a group."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST
    
    data = await request.form
    groups = current_app.config['group_manager']
    current = await groups.get(id = int(id))

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
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST
    
    groups = current_app.config['group_manager']
    data = await groups.students(int(id))
    return stringify(data), HTTPCode.OK