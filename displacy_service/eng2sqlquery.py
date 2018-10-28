class Eng2SqlQuery(object):
    def __init__(self, nlp):
        print("Eng2SqlQuery __init__")
        from .eng2sql.config import config
        self._config = config()
        self._config.nlp = nlp
        print("Eng2SqlQuery __init__ Done")

    def add_db(self, db_name, table_name):
        from .eng2sql.metadata_gen import DbUtil
        db = DbUtil(self._config.connect_str.format(db_name), table_name, self._config)
        db.build_metadata()

    def eng2sql(self, sentence):
        print("Eng2SqlQuery eng2sql")
        from .eng2sql.value_extractor import value_extractor
        print("Eng2SqlQuery eng2sql 17")
        s_list, w_list = value_extractor(self._config, sentence).keyword_finder()
        print("Eng2SqlQuery eng2sql 19 %s %s" % (str(s_list), str(w_list)))

        from .eng2sql.table_matcher import table_matcher
        print("Eng2SqlQuery eng2sql 22")
        table = table_matcher(self._config, s_list, w_list).table_extractor()
        print("Eng2SqlQuery eng2sql 24")

        from .eng2sql.col_matcher import col_matcher
        print("Eng2SqlQuery eng2sql 27")
        query = col_matcher(self._config, s_list, w_list, table).gen_query()
        print("Eng2SqlQuery eng2sql 29")

        print("Eng2SqlQuery eng2sql DONE %s " % query)
        return query
