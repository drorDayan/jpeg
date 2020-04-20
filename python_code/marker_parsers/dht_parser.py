from marker_parsers.i_parser import IParser


class HuffTree:
    def __init__(self, value=None):
        self._value = value
        self._successors = {}

    def have_kids(self):  # DROR naming
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


class HuffTable:
    def __init__(self, table_num, is_dc, tree):
        self._table_num = table_num
        self._is_dc = is_dc
        self._tree = tree

    def get_is_dc(self):
        return self._is_dc

    def get_table_id(self):
        return self._table_num
    # DROR don't we need a possibility to get a value from that tree?


class DhtParser(IParser):
    def parse(self, jpg, raw_chunk):  # DROR raw_chunk is called raw_marker in all other files
        idx = 0
        while idx < len(raw_chunk):
            # Start parsing a new table
            ht_info = raw_chunk[idx]
            table_num = ht_info & ((1 << 4) - 1)  # DROR look at DQT line 10 for example
            is_dc = ht_info & (1 << 4) > 0  # DROR look at DQT line 10 for example

            idx += 1
            symbols_of_length = raw_chunk[idx: idx + 16]  # DROR this 16 should be a const
            if (sum(symbols_of_length)) > 256:  # DROR this 256 might need to be a const
                raise Exception("Illegal Huffman table")

            idx += 16
            symbols_part_length = sum(symbols_of_length)  # DROR you use the sum twice, y?
            symbols_part = raw_chunk[idx: idx + symbols_part_length]
            huff_tree = self.generate_huff_tree(symbols_of_length, symbols_part)
            huff_table = HuffTable(table_num, is_dc, huff_tree)
            jpg.add_huffman_table(huff_table)  # DROR you used exceptions while I used return values, we should be consistent
            idx += symbols_part_length
        # DROR either use debug or remove
        print("I'm a DHT parser!")
        return True

    def generate_huff_tree(self, symbols_of_length, symbols_part):
        root = HuffTree()
        root.have_kids()

        symbol_idx = 0

        nodes_to_develop = [root.get_kid(0), root.get_kid(1)]

        for tree_level in range(1, 16 + 1):
            num_values = symbols_of_length[tree_level - 1]
            for n_val in range(num_values):
                nodes_to_develop[n_val].set_value(symbols_part[symbol_idx + n_val])
            symbol_idx += num_values

            new_parents = nodes_to_develop[num_values:]
            [new_parent.have_kids() for new_parent in new_parents]
            nodes_to_develop = [kid for parent in new_parents for kid in parent.get_kids()]

            if symbol_idx == len(symbols_part):
                break

        assert (symbol_idx == len(symbols_part))

        return root
