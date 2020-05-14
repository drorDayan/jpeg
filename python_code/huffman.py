
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

    def poop_to_jpeg(self):
        #########################################3
        #########################################
        # ASSUMING LEFTMOST TREE!
        #########################################
        ##########################################

        tree_level_nodes = [self]
        symbols_of_length = {i : 0 for i in range(1, 17)}
        symbols_list = []

        def advance_tree_level(tree_level):
            return [succ for n in tree_level for succ in n.get_kids()]

        current_level = 1
        while current_level <= 16:
            tree_level_nodes = advance_tree_level(tree_level_nodes)
            leaves = [n for n in tree_level_nodes if n.is_leaf()]
            symbols_of_length[current_level] = len(leaves)
            [symbols_list.append(leaf.get_value()) for leaf in leaves]
            current_level += 1

        return symbols_of_length, symbols_list


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
