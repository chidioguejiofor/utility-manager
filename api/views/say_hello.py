from flask_restplus import Resource
from settings import router


@router.route('/hello')
class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world', 'here': 'me'}, 400
