# TestCase
- 在conftest中编写收集用例的插件
```python
import requests


# 使用 pytest 的收集钩子，在 pytest 执行用例收集时会自动调用
def pytest_collection_modifyitems(session, config, items):
    for item in items:
        # 取出收集到的每一个用例，将用例 nodeid 和路径发送到创建用例接口，实现用例的生成
        requests.post(
            "http://localhost:5000/test_case",
            json={
                "name": item.name.encode("utf-8").decode("unicode_escape"),
                "nodeid": item.nodeid.encode("utf-8").decode("unicode_escape"),
                "description": item.fspath.strpath
            }
        )
```
- 使用 pytest collect-only 触发上述插件，收集用例

# Task
Task任务，考虑用例和用例间组织关系，对用例进行分类存储

# Suite
测试套件，解决用例和用例之间的关系，对用例运行时的管理

# Runner
执行用例

# Execution
- 利用Jenkins
- 用例拉取
- 用例执行（利用 Runner 和 Task）

# Report
测试报告解析