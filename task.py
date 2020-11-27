from quart import Blueprint, request, current_app
from utils import stringify, parse_datetime
from utils import HTTPCode
from auth import auth_needed, Auth
from managers import Student

bp = Blueprint("task", __name__, url_prefix = "/task")

@bp.route('/', methods = ['GET'])
@auth_needed(Auth.ANY, provide_obj = True)
async def get_all_tasks(auth_obj):
    """Route that gets all the tasks in the database. Any authentication necessary."""
    tasks = current_app.config['task_manager']

    if type(auth_obj) == Student:
        # Get only student's tasks
        data = await tasks.get(student_id = auth_obj.id)
        return stringify(data) if data else '', HTTPCode.OK
    else:
        # Get the teacher's tasks
        data = await tasks.get()
        return stringify(data) if data else '', HTTPCode.OK

@bp.route('/<id>', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_task(id):
    """Route that gets a task from the database. Any authentication necessary."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    tasks = current_app.config['task_manager']
    task = await tasks.get(id = int(id))
    if not task: return '', HTTPCode.NOTFOUND # TODO: Change all occurences where the item returned is '' to include a 404
    return stringify([task]), HTTPCode.OK

@bp.route('/<id>', methods = ['PATCH'])
@auth_needed(Auth.TEACHER)
async def patch_task(id):
    """Route that patches a task given its ID."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    tasks = current_app.config['task_manager']
    current = await tasks.get(id = int(id))

    data = await request.form
    title = data.get("title") or None
    description = data.get("description") or None

    if title: current.title = title
    if description: current.description = description

    max_score = data.get("max_score")
    if max_score and max_score.isdigit(): #TODO: Should group IDs be changeable?
        current.max_score = int(max_score)

    date_due = data.get("date_due")
    if date_due:
        current.date_due = parse_datetime(date_due) #TODO: Catch potential errors here, and in the same call in PUT /task/<id>

    await tasks.update(current)
    return '', HTTPCode.OK

@bp.route('/<id>', methods = ['PUT'])
@auth_needed(Auth.TEACHER)
async def patch_task(id):
    """Route that puts a task given its ID."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    data = await request.form
    title = data.get("title") or None
    description = data.get("description") or None
    max_score = data.get("max_score") or None
    date_due = data.get("date_due") or None

    if not title or not description or not max_score or not date_due or not max_score.isdigit():
        return '', HTTPCode.BADREQUEST

    tasks = current_app.config['task_manager']
    current = await tasks.get(id = int(id))
    current.title = title
    current.description = description
    current.max_score = max_score
    current.date_due = parse_datetime(date_due)

    await tasks.update(current)
    return '', HTTPCode.OK

@bp.route('/<id>', methods = ['DELETE'])
@auth_needed(Auth.TEACHER)
async def delete_task(id):
    """Route that deletes a task from the database. Teacher authentication required."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    tasks = current_app.config['task_manager']
    await tasks.delete(int(id))
    return '', HTTPCode.OK
