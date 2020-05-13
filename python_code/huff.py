
class HuffTree:
    def __init__(self, value=None):
        self._value = value
        self._successors = {}

    def create_empty_kids(self):
        assert (len(self._successors) == 0)
        left = HuffTree()
        right = HuffTree()
        self._successors = {0: left, 1: right}

    def get_kid(self, which):
        return self._successors[which]

    def get_kids(self):
        return self._successors.values()

    def set_value(self, value):
        self._value = value

    def get_value(self):
        return self._value

    def is_leaf(self):
        return len(self._successors) == 0

    def get_lookup_table(self, curr_decoded_val):
        if self.is_leaf():
            return {self._value: curr_decoded_val} if self._value is not None else {}
        ret_lookup_table = {}
        for i in [0, 1]:
            ret_lookup_table = {**ret_lookup_table, **self._successors[i].get_lookup_table(curr_decoded_val+[i])}
        return ret_lookup_table


class HuffTable:
    def __init__(self, table_num, is_dc, tree):
        self._table_num = table_num
        self._is_dc = is_dc
        self._tree = tree
        self._lookup_table = None

    def get_is_dc(self):
        return self._is_dc

    def get_table_id(self):
        return self._table_num

    def get_tree(self):
        return self._tree

    def get_lookup_table(self):
        if self._lookup_table is None:
            curr_decoded_val = []
            self._lookup_table = self._tree.get_lookup_table(curr_decoded_val)
        return self._lookup_table

    #drorda
    # FAST_POW (
    #     some things i learned in numerica and i do..
    # )