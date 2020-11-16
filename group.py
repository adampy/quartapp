from quart import Blueprint, request, current_app
from utils import stringify # Functions
from utils import HTTPCode # Enumeratons
from auth import auth_needed, Auth

bp = Blueprint("group", __name__, url_prefix = "/group")

@bp.route('/', methods = ['GET'])
@auth_needed(Auth.ANY)
async def get_groups():
    db = current_app.config['db_handler']
    data = await db.fetch("SELECT * FROM group_tbl")
    return stringify(data), HTTPCode.OK

@bp.route('/', methods = ['POST'])
@auth_needed(Auth.TEACHER, provide_obj=True)
async def make_group(auth_obj):
    db = current_app.config['db_handler']
    data = await request.form
    params = [data['name'], data['subject']]
    await db.execute("INSERT INTO group_tbl (teacher_id, name, subject) VALUES ($1, $2, $3)", auth_obj.id, *params)
    return '', HTTPCode.OK
    #params = [data['forename'], data['surname'], data['username'], data['title']] # Getting data