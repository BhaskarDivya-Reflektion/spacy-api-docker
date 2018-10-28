import sqlalchemy as sqla
import re
import pickle
import sys

import traceback

class DbUtil():
    def __init__(self, connect_string, table_name, conf):
        try:
            self.engine = sqla.create_engine(connect_string, pool_recycle=3600)
            self.conn = self.engine.connect()

            results = self.conn.execute('select current_version()').fetchone()
            print("Version returned : %s" % results[0])

            print("Connection Object %s" % str(self.conn))
 
            self.conf = conf

        except sqla.exc.OperationalError as e:
            print("SQL Connect String Incorrect : {}".format(e))
            sys.exit(1)

        self.md = sqla.MetaData(self.engine)
        self.table_name = table_name

        self.types = {}
        self.types['INTEGER'] = []
        self.types['STRING'] = []
        self.types['FLOAT'] = []
        self.types['DECIMAL'] = []
        self.types['ENUM'] = []
        self.types['DATE'] = []
        self.types['TIMESTAMP'] = []

        self.db_synonyms = []
        self.enum_columns = {}
        self.indexed_columns = []
        self.synonyms = {}

    def build_metadata(self, db_synonyms):
        #ip = input("Synonym for Database {} : ".format(self.table_name))
        self.db_synonyms = db_synonyms.split(',')
        try:
            table = sqla.Table(self.table_name, self.md, autoload=True, autoload_with=self.conn)
        except sqla.exc.NoSuchTableError:
            print("Incorrect table name {} !!!".format(self.table_name))
            sys.exit(1)

        columns = table.c

        for c in columns:
            print("INput loop for column %s %s" % (str(c.name), str(c.type)))
            if self.is_indexed(c):
                self.indexed_columns.append(c)
                self.get_synonyms(c.name)

        print("After getting all inputs")
        print("Indexed columns %s" % str(self.indexed_columns))
        print("Synonyms %s" % str(self.synonyms))
        import logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        try:
            for c in self.indexed_columns:
                print("In loop %s" % str(c))
                c_type = str(c.type)
                c_type = re.findall(r"[a-zA-Z]+", c_type)[0]
                print(c_type)

                if c_type in ['INTEGER', 'FLOAT', 'DATE', 'DECIMAL']:
                    self.types[c_type].append((c.name))
                if c_type in ['TIMESTAMP', 'DATE']:
                    self.types['DATE'].append((c.name))

                elif 'CHAR' in c_type:
                    self.types['STRING'].append((c.name))
                    # TODO better way to detect unique types threshold - should we store all ?
                    cnt = self.conn.execute("select count(distinct {}) from {};".format(c.name, self.table_name)).fetchone()
                    # if unique types are not handled with enums

                    if cnt[0] < self.conf.enum_threshold:
                        ans = self.conn.execute("select distinct({}) from {};".format(c.name, self.table_name)).fetchall()
                        self.enum_columns[(self.table_name, c.name)] = [i[0].lower() for i in ans if i[0] is not None]
                        # self.types['STRING'].remove(c.name) #
                        self.types['ENUM'].append(c.name)
                elif c_type == 'ENUM':
                    f = re.findall(r"[\w]+", str(c.type).lower())
                    self.enum_columns[(self.table_name, c.name)] = f[1:]

            print("After getting all inputs and processing them")
            idx = self.conf.tables.index(self.table_name)
            print("Going to pickle the metadata")
            self.save_to_file(self.conf.metadata_base + self.conf.databases[idx] + '_metadata.pkl')
            print("Completed pickling")
        except Exception as e:
            logger.exception(e)
            logger.exception(traceback.print_exc())

    def get_synonyms(self, c_name):
        # ip = input("Synonym for {}.{} : ".format(self.table_name, c_name))
        ip = self.conf.synonyms[self.table_name.lower()][c_name.lower()]
        doc = self.conf.nlp(ip.lower())
        # synonym_list = re.findall(r"[\w]+",str(ip).lower())
        self.synonyms[(self.table_name, c_name)] = [x.lemma_ for x in doc]

    def is_indexed(self, col):
        if col.name.lower() in self.conf.synonyms[self.table_name.lower()]:
            return True
        return False
        # ip = input("Column {} Indexed ? (y/n): ".format(col.name))
        # if ip.lower().startswith('y'):
        #     return True
        # elif ip.lower().startswith('n'):
        #     return False
        # else:
        #     print
        #     "Enter either y or n"
        #     return self.is_indexed(col)

    def print_(self):
        print(self.types)
        print(self.enum_columns)
        print(self.synonyms)

    def save_to_file(self, filename):
        with open(filename, 'wb') as fobj:
            pickle.dump([self.types, self.enum_columns, self.synonyms, self.db_synonyms], fobj)

# db = DbUtil('mysql+mysqldb://monty:mypass@localhost/{}?unix_socket=/var/run/mysqld/mysqld.sock'.format(db_name),table_name)
# db = DbUtil('mysql+mysqldb://monty:mypass@localhost/{}?unix_socket=/var/run/mysqld/mysqld.sock'.format('email'),'email')
# db.build_metadata()
# db.print_()
# db.save_to_file('actor_metadata1.pkl')
