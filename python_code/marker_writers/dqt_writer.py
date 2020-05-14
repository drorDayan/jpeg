import itertools

from marker_writers.i_writer import IWriter


class DqtWriter(IWriter):
    def __init__(self):
        super(DqtWriter, self).__init__()

    def write(self, jpeg_metadata):
        output = bytearray([0xFF, 0xDb])
        output.append(0)  # SIZE
        output.append(0)

        # IN production, don't duplicate code it's not good.
        comp_ids = jpeg_metadata.components_to_metadata.keys()
        comp_dqt_tables_indices = {i: None for i in comp_ids}

        def save_tables(table_getter, table_list):
            tables = []
            for comp_id in comp_ids:
                comp_table = table_getter(comp_id)
                x = [i for i in range(len(tables)) if (tables[i] == comp_table).all()]
                if not x:
                    table_list[comp_id] = len(tables)
                    tables.append(comp_table)
                else:
                    assert(len(x) == 1)
                    table_list[comp_id] = x[0]
            return tables

        q_ts = save_tables(lambda cid: jpeg_metadata.components_to_metadata[cid].quantization_table,
                           comp_dqt_tables_indices)
        # This code is inductively wrong

        for q_t_idx in range(len(q_ts)):
            q_t = q_ts[q_t_idx]
            q_t_data = q_t_idx
            output.append(q_t_data)
            for i, j in itertools.product(range(8), range(8)):
                output.append(int(q_t[i, j]))

        real_length = len(output) - 2
        output[2:4] = real_length.to_bytes(2, self._endianess)

        return output, comp_dqt_tables_indices
        # We're not sure what it does, but whatever it does - it works!
