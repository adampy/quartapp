from quart import Blueprint, request, current_app
from utils import stringify, parse_datetime
from utils import HTTPCode
from auth import auth_needed, Auth
from managers import Student
from exceptions import DateTimeParserError

bp = Blueprint("task", __name__, url_prefix = "/task")

@bp.route('/', methods = ['GET'])
@auth_needed(Auth.ANY, provide_obj = True)
async def get_all_tasks(auth_obj):
    """Route that gets all the tasks in the database. Any authentication necessary.
    Teacher auth -> all tasks returned
    Student auth -> student's tasks returned
    No auth -> BADREQUEST"""
    tasks = current_app.config['task_manager']
    is_completed = request.args.get("is_completed") # Should be set to True if client wants the "has_completed" attribute
    is_mine = request.args.get("mine") == "True" # Used when a teacher wants to get their own tasks TODO: Perhaps make this a default thing - make default teacher funcitonaity return only the teacher's tasks
    
    if type(auth_obj) == Student:
        # Get only student's tasks
        if is_completed == "True":
            data = await tasks.get(student_id = auth_obj.id, get_completed = True)
        else:
            data = await tasks.get(student_id = auth_obj.id)
    else:
        # Get the teacher's tasks (all the tasks from the database)
        if is_mine:
            data = await tasks.get(teacher_id = auth_obj.id)
        else:
            data = await tasks.get()

    if data:
        return stringify(data), HTTPCode.OK
    else:
        return '', HTTPCode.NOTFOUND

@bp.route('/<id>', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_task(id):
    """Route that gets a task from the database. Any authentication necessary."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    tasks = current_app.config['task_manager']
    task = await tasks.get(id = int(id))
    if not task:
        return '', HTTPCode.NOTFOUND
    return stringify([task]), HTTPCode.OK

@bp.route('/<id>', methods = ['PATCH'])
@auth_needed(Auth.TEACHER)
async def patch_task(id):
    """Route that patches a task given its ID."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    tasks = current_app.config['task_manager']
    current = await tasks.get(id = int(id))
    if not current:
        return '', HTTPCode.NOTFOUND

    data = await request.form
    title = data.get("title") or None
    description = data.get("description") or None

    if title: current.title = title
    if description: current.description = description

    max_score = data.get("max_score")
    if max_score and max_score.isdigit():
        current.max_score = int(max_score)

    date_due = data.get("date_due")
    if date_due:
        try:
            current.date_due = parse_datetime(date_due)
        except DateTimeParserError:
            return '', HTTPCode.BADREQUEST # Datetime formatted incorrectly

    await tasks.update(current)
    return '', HTTPCode.OK

@bp.route('/<id>', methods = ['PUT'])
@auth_needed(Auth.TEACHER)
async def put_task(id):
    """Route that puts a task given its ID."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    data = await request.form
    title = data.get("title") or None
    description = data.get("description") or None
    max_score = data.get("max_score") or None
    date_due = data.get("date_due") or None

    if not (title and description and date_due and max_score and max_score.isdigit()):
        return '', HTTPCode.BADREQUEST

    tasks = current_app.config['task_manager']
    current = await tasks.get(id = int(id))
    if not current:
        return '', HTTPCode.NOTFOUND
    current.title = title
    current.description = description
    current.max_score = max_score
    try:
        current.date_due = parse_datetime(date_due)
    except DateTimeParserError:
        return '', HTTPCode.BADREQUEST

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

# -- MARKS --
@bp.route('/<id>/status', methods = ['GET', 'POST'])
@auth_needed(Auth.STUDENT, provide_obj = True)
async def task_completed(id, auth_obj):
    """Route that sets a task to completed for a given student. This route must have a 
    'completed' field in the form-data if the task is completed. If not given, this defaults to False."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    tasks = current_app.config['task_manager']
    task_id = int(id)
    
    if request.method == "POST":
        form = await request.form
        completed = True if form.get("completed") == "true" else False

        try:
            await tasks.student_completed(completed, auth_obj.id, task_id)
            return '', HTTPCode.OK
        except PermissionError:
            return '', HTTPCode.UNAUTHORIZED # Unauthorized to change other peoples task statuses

    elif request.method == "GET":
        marks = current_app.config['mark_manager']
        mark = await marks.get(student_id = auth_obj.id, task_id = task_id)
        if mark:
            return stringify([mark]), HTTPCode.OK
        else:
            return '', HTTPCode.NOTFOUND

@bp.route('/<id>/current_feedback', methods = ['GET'])
@auth_needed(Auth.TEACHER)
async def teacher_get_current_feedback(id):
    """Route that returns pre-existing feedback for a student and a task. The student_id is given as a query string parameter under `student`."""
    studentid = request.args.get("student")
    if not id.isdigit() or not student_id.isdigit():
        return '', HTTPCode.BADREQUEST

    marks = current_app.config['mark_manager']
    mark = await marks.get(student_id = int(student_id), task_id = int(id))
    if mark:
        return stringify([mark]), HTTPCode.OK
    else:
        return '', HTTPCode.NOTFOUND

@bp.route('/<id>/mark', methods = ['GET'])
@auth_needed(Auth.TEACHER)
async def get_task_marks(id):
    """Gets all the marks avaliable for the given task. This route can be used to see who has completed a task, too."""
    if not id.isdigit():
        return '', HTTPCode.BADREQUEST

    marks = current_app.config['mark_manager']
    data = await marks.get(task_id = int(id))
    if not data:
        return '', HTTPCode.NOTFOUND
    else:
        return stringify([data]), HTTPCode.OK
    

@bp.route('/<id>/provide_feedback', methods = ['POST'])
@auth_needed(Auth.TEACHER, provide_obj = True)
async def prov_feedback(id, auth_obj):
    data = await request.form
    student_id = data.get("student") or None
    score = data.get("score") or None
    feedback = data.get("feedback") or None

    if not student_id or not student_id.isdigit() or not id.isdigit() or not score or not score.isdigit() or not feedback:
        return '', HTTPCode.BADREQUEST
    
    student_id = int(student_id)
    task_id = int(id)
    score = int(score)
    
    try:
        tasks = current_app.config['task_manager']
        await tasks.provide_feedback(feedback, score, student_id, task_id, auth_obj)
        return '', HTTPCode.OK
    except PermissionError:
        return '', HTTPCode.UNAUTHORIZED # Teacher cannot provide feedback to tasks they have not set