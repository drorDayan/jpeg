from marker_writers.i_writer import IWriter


class DhtWriter(IWriter):
    def write(self, jpeg_metadata):
        comp_ids = jpeg_metadata.components_to_metadata.keys()
        comp_ac_tables_indices = {i: None for i in comp_ids}
        comp_dc_tables_indices = {i: None for i in comp_ids}

        def save_huff_tables(table_getter, table_list):
            tables = []
            for comp_id in comp_ids:
                comp_table = table_getter()
                if comp_table not in tables:
                    table_list[comp_id] = len(tables)
                    tables.append(comp_table)
                else:
                    table_list[comp_id] = tables.index(comp_table)
            return tables

        ac_t = save_huff_tables(lambda cid: jpeg_metadata.components_to_metadata[cid].ac_huffman_table,
                                comp_ac_tables_indices)
        dc_t = save_huff_tables(lambda cid: jpeg_metadata.components_to_metadata[cid].dc_huffman_table,
                                comp_dc_tables_indices)

        output = bytearray()
        output.append(0xFF)  # DHT marker
        output.append(0xC4)
        output.append(0)  # Marker size
        output.append(0)

        def poop_tables(table_list, ac_dc_bit):
            for table_index in range(len(table_list)):
                table = table_list[table_index]

                ht_info = (ac_dc_bit << 4) + table_index  # 1 for AC
                output.append(ht_info)
                tree_thing = table.get_tree()
                num_symbols_of_length, symbols_of_really = tree_thing.poop_to_jpeg()

                for n in num_symbols_of_length:
                    output.append(n)
                for sym in symbols_of_really:
                    output.append(sym)

        poop_tables(ac_t, 1)
        poop_tables(dc_t, 0)

        real_length = len(output) - 2
        output[2:4] = real_length.to_bytes(2, self._endianess)

        return output, comp_ac_tables_indices, comp_dc_tables_indices

    def __init__(self):
        super(DhtWriter, self).__init__()
