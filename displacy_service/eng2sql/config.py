class config():
    def __init__(self):
        self.load_metadata = False

        self.enum_threshold = 20

        # don't change if using MySQL DB
        #self.db_type = 'mysql+mysqldb://'
        self.db_type = 'snowflake://'

        
        # database connect string
        #self.connect_str = 'monty:mypass@localhost/{}?unix_socket=/var/run/mysqld/mysqld.sock'
        self.connect_str = 'dev_etl_user:PASS@bh95352.us-east-1/RFK_DEV/{}/?warehouse=dev_etl_wh?role=dev_etl_role'

        # List the databse names in the database server , and the *corresponsing* table names you want to search on
        # For ex: 'imdb' database schema has the 'movies' db
        self.databases = ['ANALYTICS']
        self.tables = ['product_analytics']

        # staford parser home directory
        self.stanford_parser_home = '/app/stanford-parser-full-2018-10-17/'

        self.connect_str = self.db_type + self.connect_str

        # filename = db_name+'-metadata.pkl'
        # metadata_files = ['usaa_metadata.pkl','imdb_metadata.pkl','employees_metadata.pkl']
        self.metadata_base = '/app/metadata_files/'

        aggregate_map = {}
        aggregate_map['average', 'mean'] = 'AVG('
        aggregate_map['top', 'highest', 'maximum', 'most'] = 'MAX('
        aggregate_map['least', 'lowest', 'minimum'] = 'MIN('
        aggregate_map['total', 'sum'] = 'SUM('

        self.aggregate_map = aggregate_map

        self.select_words = [u'show', u'select', u'tell', u'search', u'find', u'list', u'display', u'get', u'retrieve',
                             u'return']
        self.operator_high_words = [u'more than', u'greater than', u'above', u'over', u'higher than', u'at least',
                                    u'longer than', u'taller than']  # taller, longer # TODO handle longer with time
        self.operator_low_words = [u'less than', u'lesser than', u'below', u'under', u'lower than', u'at most',
                                   u'fewer than', u'shorter than']
        self.operator_equal_words = [u'is equal to', u'equals']
        # time_high_words = [u'after',u'since']
        # time_low_words = [u'before',u'till']
        self.time_words = [u'after', u'since', u'before', u'till']
        self.group_words = [u'per', u'for each', u'across', u'grouped by', u'in each', u'seggregated by']
