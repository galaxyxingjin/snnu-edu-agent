"""utils 兼容层

coze_coding_utils 内部部分模块使用 ``from utils.helper import ...``、
``from utils.log.loop_trace import ...`` 的写法（``utils`` 为其历史别名）。
本项目通过 PYTHONPATH 暴露了 ``src/utils`` 这个 ``utils`` 包，因此需要将
相关子模块转发到 ``coze_coding_utils`` 的对应模块，保证运行期导入一致。
"""
import importlib
import sys

_ALIASES = {
    "utils.helper": "coze_coding_utils.helper",
    "utils.log": "coze_coding_utils.log",
    "utils.log.loop_trace": "coze_coding_utils.log.loop_trace",
}

for _alias, _target in _ALIASES.items():
    try:
        sys.modules.setdefault(_alias, importlib.import_module(_target))
    except ImportError:
        pass