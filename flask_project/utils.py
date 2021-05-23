from jenkinsapi.jenkins import Jenkins


def run_jenkins(account, password, job, command):
    """
    使用jenkins运行用例
    :param account: 账号名
    :param password: 密码
    :param job: 需要运行的job
    :param command: 执行的命令
    :return:
    """
    J = Jenkins('http://114.215.19.208:8080/', username=account, password=password)
    J[job].invoke(build_params={"command": command})
