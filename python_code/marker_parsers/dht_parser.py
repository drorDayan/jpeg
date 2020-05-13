from jpeg_common import *
from marker_parsers.i_parser import IParser
from huff import *


class DhtParser(IParser):
    max_symbol_length = 16
    max_num_symbols = 256

    def parse(self, jpg, raw_marker):
        info_print("DHT parser started")
        idx = 0
        while idx < len(raw_marker):
            # Start parsing a new table
            ht_info = raw_marker[idx]
            table_num = ht_info & 0x0F
            is_dc = (ht_info & 0x10) == 0
            if (ht_info & 0b11100000) != 0:
                raise Exception("Illegal Huffman Table information byte")

            idx += 1
            symbols_of_length = raw_marker[idx: idx + self.max_symbol_length]
            if (sum(symbols_of_length)) > self.max_num_symbols:
                raise Exception("Illegal Huffman table")

            idx += 16
            symbols_part_length = sum(symbols_of_length)
            symbols_part = raw_marker[idx: idx + symbols_part_length]
            huff_tree = self.generate_huff_tree(symbols_of_length, symbols_part)
            huff_table = HuffTable(table_num, is_dc, huff_tree)
            print(huff_table.get_lookup_table())
            jpg.add_huffman_table(huff_table)
            idx += symbols_part_length

        info_print("DHT parser ended successfully")
        return True

    @staticmethod
    def generate_huff_tree(symbols_of_length, symbols_part):
        root = HuffTree()
        root.create_empty_kids()

        symbol_idx = 0

        nodes_to_develop = [root.get_kid(0), root.get_kid(1)]

        for tree_level in range(16):
            num_values = symbols_of_length[tree_level]
            for n_val in range(num_values):
                nodes_to_develop[n_val].set_value(symbols_part[symbol_idx + n_val])
            symbol_idx += num_values

            new_parents = nodes_to_develop[num_values:]
            [new_parent.create_empty_kids() for new_parent in new_parents]
            nodes_to_develop = [kid for parent in new_parents for kid in parent.get_kids()]

            # this optimization is to prevent a full tree build when we only use part of it's levels
            if symbol_idx == len(symbols_part):
                break

        assert (symbol_idx == len(symbols_part))

        return root
