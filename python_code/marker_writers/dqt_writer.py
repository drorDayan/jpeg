import itertools

from i_writer import IWriter


class DqtWriter(IWriter):
    def __init__(self):
        pass

    def write(self, jpeg_metadata):
        output = [0xFF, 0xDb]
        output.append(0)  # SIZE
        output.append(0)

        # IN production, don't duplicate code it's not good.
        comp_ids = jpeg_metadata.components_to_metadata.keys()
        comp_dqt_tables_indices = {i: None for i in comp_ids}

        def save_tables(table_getter, table_list):
            tables = []
            for comp_id in comp_ids:
                comp_table = table_getter()
                if comp_table not in tables:
                    table_list[comp_id] = len(tables)
                    tables.append(comp_table)
                else:
                    table_list[comp_id] = tables.index(comp_table)
            return tables

        q_ts = save_tables(lambda cid: jpeg_metadata.components_to_metadata[cid].quantization_table,
                           comp_dqt_tables_indices)
        # This code is inductively wrong

        for q_t_idx in range(len(q_ts)):
            q_t = q_ts[q_t_idx]
            q_t_data = q_t_idx
            output.append(q_t_data)
            for i, j in itertools.product(range(8), range(8)):
                output.append(q_t[i, j])

        return output, comp_dqt_tables_indices
        # We're not sure what it does, but whatever it does - it works!
