from flask import Flask
from flask import request
from flask import jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource
from flask_restful import Api
from flask_project.utils import run_jenkins

app = Flask(__name__)
CORS(app)
api = Api(app)


class Config(object):
    """配置信息"""
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@127.0.0.1:3306/flask_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    JSON_AS_ASCII = False


app.config.from_object(Config)
db = SQLAlchemy(app)


class UserTable(db.Model):
    """用户表模型类"""
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    account = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=False, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.account


class TestCaseTable(db.Model):
    """用例表"""
    __tablename__ = "test_case"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    nodeid = db.Column(db.String(512), unique=True, nullable=False)  # 用例的唯一标识,使用 nodeid 运行用例
    description = db.Column(db.String(1024), unique=False, nullable=True)

    def as_dict(self):
        return {"id": self.id, "nodeid": self.nodeid, "description": self.description}

    def __repr__(self):
        return '<TestCase %r>' % self.nodeid


class TaskTable(db.Model):
    """任务表"""
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    description = db.Column(db.String(1024), unique=False, nullable=True)


class TaskJoinTestCaseTable(db.Model):
    """任务与用例的关联表"""
    __tablename__ = "task_join_testcase"
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(80), unique=False, nullable=False)
    testcase_id = db.Column(db.String(80), unique=False, nullable=False)


class Login(Resource):
    """登录"""
    def post(self):
        req_dict = request.get_json()
        tc = UserTable.query.filter_by(account=req_dict.get('account')).all()
        if not tc:
            return jsonify(content="error", errcode=404, message="用户不存在")
        else:
            for t in tc:
                if req_dict.get("account") == t.account and req_dict.get("password") == t.password:
                    return jsonify(content="ok", errcode=0)
                else:
                    return jsonify(content="error", errcode=404, message="密码错误")


class Register(Resource):
    """注册"""
    def post(self):
        account = request.json.get('account')
        password1 = request.json.get('password1')
        password2 = request.json.get('password2')
        u = UserTable.query.filter(account=account).first()
        if len(account) > 80:
            return jsonify(content="error", errcode=404, message="用户名过长")
        if password1 != password2:
            return jsonify(content="error", errcode=404, message="两次密码不一致")
        if u:
            return jsonify(content="error", errcode=404, message="用户名已经存在")
        user = UserTable(account=account, password=password1)
        db.session.add(user)
        db.session.commit()
        return jsonify(content="ok", errcode=0)


class TestCaseServer(Resource):
    """查看用例与保存用例"""
    def get(self):
        """查询测试用例"""
        tc = TestCaseTable.query.all()
        json_data = []
        for t in tc:
            result = {
                'name': t.name,
                'nodeid': t.nodeid,
                'description': t.description
            }
            json_data.append(result)
        return json_data

    def post(self):
        """存储测试用例"""
        test_case = TestCaseTable(**request.json)
        db.session.add(test_case)
        db.session.commit()
        return jsonify(content="ok", errcode=0)

    def put(self):
        """更新用例"""
        if "name" in request.json:
            testcase = TestCaseTable.query.filter_by(id=request.json.get('id')).first()
            testcase.name = request.json.get("name")
            testcase.nodeid = request.json.get("nodeid")
            testcase.description = request.json.get("description")
            db.session.commit()
            return jsonify(content="ok", errcode=0)


class CreateTask(Resource):
    """用于生成任务"""
    def post(self):
        # 请任务的 id 放到 url 的参数中
        id = request.args.get("id")
        # 将任务的描述信息放到请求体中
        name = request.json.get("name")
        description = request.json.get("description")
        task = TaskTable(id=id, name=name, description=description)
        db.session.add(task)
        db.session.commit()
        tk = TaskTable.query.filter_by(id=id).first()
        if not tk:
            return jsonify(content="error", errcode=404, message="任务创建失败")
        else:
            return jsonify(content="ok", errcode=0)


class TaskServe(Resource):
    """处理任务和用例的关系"""
    def post(self):
        # 把任务跟用例对应
        task_case = TaskJoinTestCaseTable(**request.json)
        db.session.add(task_case)
        db.session.commit()
        return jsonify(content="ok", errcode=0)


class RunTask(Resource):
    """运行测试用例"""
    def post(self):
        if "task_id" not in request.json:
            return jsonify(content="error", errcode=404, message="no task id")
        task_id = request.json.get("task_id")
        task_join_testcases = TaskJoinTestCaseTable.query.filter_by(task_id=task_id).all()
        nodeids = []
        for task_join_testcase in task_join_testcases:
            testcase_id = task_join_testcase.testcase_id
            testcase = TestCaseTable.query.filter_by(id=testcase_id).first()
            nodeids.append(testcase.nodeid)
        command = "pytest " + " ".join(nodeids)
        run_jenkins(
            request.json.get("account"),
            request.json.get("password"),
            request.json.get("job"),
            command)
        return jsonify(content="ok", errcode=0)


api.add_resource(TestCaseServer, '/test_case')
api.add_resource(Login, '/login')
api.add_resource(Register, '/register')
api.add_resource(CreateTask, '/create_task')
api.add_resource(TaskServe, '/task')
api.add_resource(RunTask, '/run_task')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
    # db.drop_all()
    # db.create_all()

