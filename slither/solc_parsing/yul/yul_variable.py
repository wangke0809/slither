import logging

from slither.core.variables.local_variable import LocalVariable

logger = logging.getLogger("YulVariable")


class YulVariable(LocalVariable):

    def __init__(self, var):
        super(LocalVariable, self).__init__()

        assert(var['nodeType'] == 'YulTypedName')

        self._name = var['name']
        self.reference_id = None
        self._location = 'memory'
        self.set_type('uint256')

    pass
