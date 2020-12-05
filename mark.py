from quart import Blueprint, request, current_app
from utils import stringify
from utils import HTTPCode
from auth import auth_needed, Auth

bp = Blueprint("mark", __name__, url_prefix = "/mark")

@bp.route('/', methods = ["GET"])
@auth_needed(Auth.STUDENT)
async def get_marks():
    """Abstract interface between the data and the user. Either `group`, `task`, `student`, `mark` must be
    noted in the form-data of the request."""
    data = await request.form
    marks = current_app.config['mark_manager']

    student_id = data.get("student") or None
    group_id = data.get("group") or None
    task_id = data.get("task") or None
    mark_id = data.get("mark") or None

    if student_id:
        data = await marks.get(student_id = student_id)
        return stringify([data]), HTTPCode.OK
    elif group_id:
        data = await marks.get(group_id = group_id)
        return stringify([data]), HTTPCode.OK
    elif task_id:
        data = await marks.get(task_id = task_id)
        return stringify([data]), HTTPCode.OK
    elif mark_id:
        data = await marks.get(mark_id = mark_id)
        return stringify([data]), HTTPCode.OK
    else:
        return '', HTTPCode.BADREQUEST
