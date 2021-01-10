from quart import Blueprint, request, current_app
from utils import stringify
from utils import HTTPCode
from auth import auth_needed, Auth

bp = Blueprint("mark", __name__, url_prefix = "/mark")

@bp.route('/', methods = ["GET"])
@auth_needed(Auth.ANY)
async def get_marks():
    """Abstract interface between the data and the user. Either `group`, `task`, `student`, `mark` must be
    noted in the query string of the request."""
    marks = current_app.config['mark_manager']

    student_id = request.args.get("student") or None
    group_id = request.args.get("group") or None
    task_id = request.args.get("task") or None
    mark_id = request.args.get("mark") or None

    if student_id:
        if not student_id.isdigit():
            return '', HTTPCode.BADREQUEST
        data = await marks.get(student_id = int(student_id))
        return stringify(data), HTTPCode.OK
    
    elif group_id:
        if not group_id.isdigit():
            return '', HTTPCode.BADREQUEST
        data = await marks.get(group_id = int(group_id))
        return stringify(data), HTTPCode.OK
    
    elif task_id:
        if not task_id.isdigit():
            return '', HTTPCode.BADREQUEST
        data = await marks.get(task_id = int(task_id))
        return stringify(data), HTTPCode.OK
    
    elif mark_id:
        if not mark_id.isdigit():
            return '', HTTPCode.BADREQUEST
        data = await marks.get(mark_id = int(mark_id))
        return stringify(data), HTTPCode.OK
    
    else:
        return '', HTTPCode.BADREQUEST
