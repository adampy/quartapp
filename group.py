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
    data = await request.form
    name = data.get('name') or None
    subject = data.get('subject') or None

    if not name or not subject:
        return '', HTTPCode.BADREQUEST # Not all necessary arguments given

    groups = current_app.config['group_manager']
    await groups.create(auth_obj.id, data['name'], data['subject'])
    return '', HTTPCode.CREATED
