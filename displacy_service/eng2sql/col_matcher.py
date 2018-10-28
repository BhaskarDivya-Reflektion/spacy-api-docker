import pickle
import parsedatetime

cal = parsedatetime.Calendar()


class utils():
    def __init__(self, conf):
        self.conf = conf

    def get_agg_func(self, select_clause, done_words):
        for word in select_clause:
            if word.text in [u'many', u'number']:
                done_words.add(word.i)
                return 'COUNT(', done_words
            if word.pos_ == u'ADJ':
                for k in self.conf.aggregate_map:
                    if word.lemma_ in k:
                        done_words.add(word.i)
                        return self.conf.aggregate_map[k], done_words
            # TODO handle oldest, largest here
            if word.tag_ == u'JJS':
                done_words.add(word.i)
                return 'MAX(', done_words

        return '', done_words

    def parse_time(self, col, op, date_value):
        # TODO use range library

        if date_value.isdigit() and int(date_value) > 1900 and int(date_value) < 2100:
            col = "DATE_FORMAT({}, '%Y')".format(col)
            val = date_value
            return col, op, val

        doc = self.conf.nlp(date_value, entity=False)
        for w in doc:
            if w.dep_ == u'ROOT':
                root_w = w.text.encode('utf-8')

        # deals with only year
        if 'year' in root_w:
            col = "DATE_FORMAT('{}', '%Y')".format(col)
            val = "%s" % cal.parseDT(date_value)[0]
            # val = "DATE_FORMAT('{}', '%Y')".format(val)
            val = val[:4]
            return col, op, val

        # TODO remove ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec','month']
        # only month
        for m in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'month']:
            if m in root_w.lower():
                col = "DATE_FORMAT('{}', '%Y%m')".format(col)
                val = "%s" % cal.parseDT(date_value)[0]
                val = "DATE_FORMAT('{}', '%Y%m')".format(val)
                return col, op, val

        for m in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 'day']:
            if m in root_w.lower():
                col = "DATE_FORMAT('{}', '%Y%m%d')".format(col)
                val = "%s" % cal.parseDT(date_value)[0]
                val = "DATE_FORMAT('{}', '%Y%m%d')".format(val)
                return col, op, val

        # handle last week
        if 'week' in root_w:
            col = "DATE_FORMAT('{}', '%X%V')".format(col)
            val = "%s" % cal.parseDT(date_value)[0]
            val = "DATE_FORMAT('{}', '%X%V')".format(val)
            return col, op, val


class col_matcher():
    def __init__(self, conf, S_LIST, W_LIST, table):
        self.conf = conf
        self.done_words = set()
        self.S_LIST = S_LIST
        self.W_LIST = W_LIST
        self.types = {}
        self.enum_columns = {}
        self.col_synonyms = {}
        self.db_synonyms = []
        self.table = table

    def get_select_col(self):
        S_LIST = list(self.S_LIST[0])
        S_words = [x for x in S_LIST if x.text not in [u'many', u'number']]
        if len(S_words) != len(S_LIST):
            return '*'

        S_words = [x for x in S_words if x.pos_ == u'NOUN']
        if len(S_words) == 0:
            S_words = S_LIST

        S_words = [x.lemma_ for x in S_words]

        col_matches = []
        for word in S_words:
            for k in self.col_synonyms:
                if any(s.lower() == word for s in self.col_synonyms[k]):
                    col_matches.append(k[1])

        if len(col_matches) == 1:
            return col_matches[0]
        elif len(col_matches) > 1:
            s = set([x for x in col_matches if col_matches.count(x) > 1])
            if len(s) == 1:
                return list(s)[0]
            elif len(s) > 1:
                # if more than one duplicate
                # TODO temp solution
                st = ''
                for c in s:
                    st += c + ','
                return st

            elif len(col_matches) > 0:
                # TODO temp solution
                st = ''
                for c in col_matches:
                    st += c + ','
                return st

        print
        '-- -- ', S_words[0], self.db_synonyms
        if len(S_words) == 1 and S_words[0] in self.db_synonyms:
            return '*'

        col_str = ' '.join(S_words)
        max_col = self.word2vec_column_matcher(col_str)

        return max_col

    def get_where_col(self):
        T_LIST = self.S_LIST + self.W_LIST
        where_tupl_list = []
        # print T_LIST
        for tupl in T_LIST:

            t = list(tupl)

            sub_phrase_list = [t[m:n + 1] for m in range(0, len(t)) for n in range(m, len(t))]
            sub_phrase_list.sort(key=lambda x: len(x), reverse=True)

            for sub_phrase in sub_phrase_list:
                # if len(sub_phrase)==1 and sub_phrase[0].lemma_ == u'start':
                # 	op = ' like '
                # 	i = sub_phrase[0].i
                # 	doc = sub_phrase[0].doc
                # 	assert(doc[i+1].text == u'with')
                # 	for c in doc[i+1].children:
                # 		val = c.text + '%'
                # 	# TODO make the context
                # 	# TODO
                # 	context_str = 'actor'
                # 	col = self.word2vec_column_matcher(context_str)
                # 	where_tupl_list.append((col,op,val))

                to_continue = False
                idx = [w.i for w in sub_phrase]
                if self.done_words.intersection(set(idx)) != set([]):
                    continue

                phrase = ' '.join([w.lemma_ for w in sub_phrase])

                for k in self.enum_columns:
                    # lemma is purchase - value is purchased
                    # TODO match lemma of both
                    # print type(phrase)
                    # print self.enum_columns[k]
                    if any(s.lower() == phrase.encode('utf-8') for s in self.enum_columns[k]):
                        for w in sub_phrase:
                            self.done_words.add(w.i)
                        idx = T_LIST.index(tupl)
                        if len(T_LIST[idx - 1]) == 1 and T_LIST[idx - 1][0].dep_ == u'neg':
                            where_tupl_list.append((k[1], '!=', phrase))
                        else:
                            where_tupl_list.append((k[1], '=', phrase))
                        to_continue = True
                        break

                if to_continue:
                    continue

                type_tupl = None
                # TODO while loop to get phrase
                # print sub_phrase[0].ent_type_, sub_phrase[0].ent_iob , sub_phrase[0].text
                if sub_phrase[0].ent_type_ == u'DATE' and sub_phrase[-1].ent_type_ == u'DATE' and sub_phrase[
                    0].ent_iob == 3:
                    type_tupl = self.match_type('DATE', tupl, sub_phrase, T_LIST)
                elif sub_phrase[0].ent_type_ in [u'GPE', u'LOC'] and sub_phrase[-1].ent_type_ in [u'GPE', u'LOC'] and \
                                sub_phrase[0].ent_iob == 3:
                    type_tupl = self.match_type('GPE', tupl, sub_phrase, T_LIST)
                elif sub_phrase[0].ent_type_ == u'PERSON' and sub_phrase[-1].ent_type_ == u'PERSON' and sub_phrase[
                    0].ent_iob == 3:
                    type_tupl = self.match_type('PERSON', tupl, sub_phrase, T_LIST)
                elif sub_phrase[0].ent_type_ == u'LANGUAGE' and sub_phrase[-1].ent_type_ == u'LANGUAGE':
                    type_tupl = self.match_type('LANGUAGE', tupl, sub_phrase, T_LIST)
                elif sub_phrase[0].tag_ == u'CD' and sub_phrase[-1].tag_ == u'CD':
                    type_tupl = self.match_type('INT', tupl, sub_phrase, T_LIST)

                if type_tupl != None:
                    for w in sub_phrase:
                        self.done_words.add(w.i)
                    where_tupl_list.append(type_tupl)

        return where_tupl_list

    def get_group_col(self):
        group_cols = []
        for tupl in self.W_LIST:
            # assuming first word in tuple would be per - for group by - no exceptions found so far
            if tupl[0].text == u'per':
                tupl = tupl[1:]
                col_str = " ".join([x.text for x in tupl])
                col = self.word2vec_column_matcher(col_str)
                for w in tupl:
                    self.done_words.add(w.i)
                group_cols.append(col)
                # return col
        if len(group_cols) > 0:
            return group_cols
        else:
            return False

    def get_order_col(self):
        order_query = ' ORDER BY '
        asc_query = ' DESC'
        limit_query = ' LIMIT '
        is_order = False

        for tupl in self.W_LIST:
            if tupl[0].text == u'limit':
                limit_query += tupl[1].text
                self.done_words.add(tupl[1].i)

            if tupl[0].text == u'asc':
                asc_query = ' ASC'
                self.done_words.add(tupl[1].i)

            if tupl[0].text == u'order':
                is_order = True
                tupl = tupl[1:]
                col_str = " ".join([x.lemma_ for x in tupl])
                col = self.word2vec_column_matcher(col_str)
                order_query += col
                for w in tupl:
                    self.done_words.add(w.i)

        if is_order:
            return order_query + asc_query + limit_query
        else:
            return ''

    def match_type(self, ner, tupl, sub_phrase, T_LIST):
        more_w = set(['more', 'after', 'since'])
        less_w = set(['less', 'before', 'till'])

        print
        ner, sub_phrase
        # print tupl

        if more_w.intersection(set([w.lemma_ for w in tupl])) != set([]):
            op = '>'
            sub_phrase = [x for x in sub_phrase if x.lemma_ not in more_w]
        elif less_w.intersection(set([w.lemma_ for w in tupl])) != set([]):
            op = '<'
            sub_phrase = [x for x in sub_phrase if x.lemma_ not in less_w]
        else:
            op = '='

        val = ' '.join([w.text for w in sub_phrase])

        if ner == 'DATE':
            date_cols = self.types['DATE']
            if len(date_cols) == 1:
                col = date_cols[0]
                return utils(self.conf).parse_time(col, op, val)
            elif len(date_cols) == 0:
                candidates = self.types['INTEGER']
            else:
                candidates = date_cols

            # past two T_LIST - take nouns
            idx = T_LIST.index(tupl)
            if len(T_LIST[idx - 1]) == 1 and T_LIST[idx - 1][0].dep_ == u'neg':
                op = '!='
            context = T_LIST[idx - 2:idx]
            context_str = ''
            for t in context:
                for w in t:
                    if w.pos_ == u'NOUN' or w.pos_ == u'VERB':
                        context_str += w.lemma_ + ' '

            ner_str = u'date year month time'
            max_col = self.word2vec_column_matcher(ner_str + ' ' + context_str, candidates)
            return utils(self.conf).parse_time(max_col, op, val)

        elif ner == 'GPE':
            print
            self.types
            str_cols = self.types['STRING']
            if len(str_cols) == 1:
                col = str_cols[0]
                return (col, op, val)
            elif len(str_cols) == 0:
                print
                'No String Col Found!'
            else:
                candidates = str_cols

                # past two T_LIST - take nouns
            idx = T_LIST.index(tupl)
            if len(T_LIST[idx - 1]) == 1 and T_LIST[idx - 1][0].dep_ == u'neg':
                op = '!='
            context = T_LIST[idx - 2:idx + 1]
            context_str = ''
            for t in context:
                for w in t:
                    if w.pos_ == u'NOUN' or w.pos_ == u'VERB':
                        context_str += w.lemma_ + ' '
                        # context_str += ' '.join(list(t))

            ner_str = u'state country location city'
            max_col = self.word2vec_column_matcher(ner_str + ' ' + context_str, candidates)

            return (max_col, op, val)

        elif ner == 'PERSON':
            str_cols = self.types['STRING']
            if len(str_cols) == 1:
                col = str_cols[0]
                return (col, op, val)
            elif len(str_cols) == 0:
                print
                'No String Col Found!'
            else:
                candidates = str_cols

                # past two T_LIST - take nouns
                # take -2 and + tupl including itself for person -- remove proper nouns
            idx = T_LIST.index(tupl)
            if len(T_LIST[idx - 1]) == 1 and T_LIST[idx - 1][0].dep_ == u'neg':
                op = '!='
            context = T_LIST[idx - 2:idx + 1]
            context_str = ''
            for t in context:
                for w in t:
                    if w.pos_ == u'NOUN' or w.pos_ == u'VERB':
                        context_str += w.lemma_ + ' '

            ner_str = u'name person human'
            max_col = self.word2vec_column_matcher(ner_str + ' ' + context_str, candidates)

            return (max_col, op, val)

        elif ner == 'LANGUAGE':
            str_cols = self.types['STRING']
            if len(str_cols) == 1:
                col = str_cols[0]
                return (col, op, val)
            elif len(str_cols) == 0:
                print
                'No String Col Found!'
            else:
                candidates = str_cols

            ner_str = u'language english french hindi'
            max_col = self.word2vec_column_matcher(ner_str, candidates)

            return (max_col, op, val)
        # simple w2v match

        elif ner == 'INT':
            int_cols = self.types['INTEGER'] + self.types['FLOAT']
            if len(int_cols) == 1:
                col = int_cols[0]
                return (col, op, val)
            elif len(int_cols) == 0:
                print
                'No Int Col Found!'
            else:
                candidates = int_cols

            # only take previous tuples - integer modifier will be on the left - TODO exceptions, weight
            idx = T_LIST.index(tupl)
            if len(T_LIST[idx - 1]) == 1 and T_LIST[idx - 1][0].dep_ == u'neg':
                op = '!='
            context = T_LIST[idx - 2:idx]  # + T_LIST[idx+1:idx+3]
            context_str = ''
            for t in context:
                for w in t:
                    if w.pos_ == u'NOUN' or w.pos_ == u'VERB':
                        context_str += w.lemma_ + ' '
            max_col = self.word2vec_column_matcher(context_str, candidates)

            return (max_col, op, val)

    def word2vec_column_matcher(self, match_str, candidates=None):
        match_doc = self.conf.nlp(match_str)
        max_sim = 0.0
        max_col = None

        if candidates == None:
            for k in self.col_synonyms:
                doc = self.conf.nlp(' '.join(self.col_synonyms[k]))
                sim = doc.similarity(match_doc)
                # print k[1], sim, match_doc, doc
                if sim > max_sim:
                    max_sim = sim
                    max_col = k[1]

        else:
            for c in candidates:
                k = (self.table, c)
                doc = self.conf.nlp(' '.join(self.col_synonyms[k]))
                sim = doc.similarity(match_doc)
                # print sim,c
                if sim > max_sim:
                    max_sim = sim
                    max_col = c

        return max_col

    def gen_query(self):
        idx = self.conf.tables.index(self.table)
        filename = self.conf.metadata_base + self.conf.databases[idx] + '_metadata.pkl'
        with open(filename, 'rb') as f:
            md = pickle.load(f)
            self.types = md[0]
            self.enum_columns = md[1]
            self.col_synonyms = md[2]
            self.db_synonyms = md[3]
        # print types
        QUERY_1 = 'SELECT '
        QUERY_2 = ' FROM '
        QUERY_3 = ' WHERE '
        QUERY_4 = ''

        assert (len(self.S_LIST) == 1)
        select_clause = list(self.S_LIST[0])
        aggr_func, self.done_words = utils(self.conf).get_agg_func(select_clause, self.done_words)
        col_name = self.get_select_col()
        group_cols = self.get_group_col()

        QUERY_4 = self.get_order_col()

        if aggr_func != '':
            QUERY_1 += str(aggr_func) + str(col_name) + ')'
        else:
            QUERY_1 += str(col_name)

        QUERY_2 += str(self.table)

        where_tupl_list = self.get_where_col()
        if len(where_tupl_list) == 0:
            QUERY_3 = ''
        for t in where_tupl_list:
            if where_tupl_list.index(t) != 0:
                QUERY_3 += ' and '
            QUERY_3 += t[0] + t[1] + t[2]

        if group_cols:
            QUERY_3 += ' GROUP BY ' + ','.join(group_cols)
            QUERY_1 += ',' + ','.join(group_cols)

        print
        ''
        print
        ''
        print
        'QUERY >>>', QUERY_1 + QUERY_2 + QUERY_3 + QUERY_4
        print
        ''

        done_words = set()
        table = ''

        return QUERY_1 + QUERY_2 + QUERY_3
