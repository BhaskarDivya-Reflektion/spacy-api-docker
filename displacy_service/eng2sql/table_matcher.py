import pickle

from .metadata_gen import DbUtil


# ignore num and date
# ignore verb if root lemma is be
def is_filter_word(word):
    if word.ent_type_ in [u'DATE', u'GPE', u'PERSON', u'TIME']:
        return False
    elif word.like_num or word.tag_ == u'NNP' or word.lemma_ == u'be':
        return False
    else:
        return True


class table_matcher():
    def __init__(self, conf, S_LIST, W_LIST):
        print("Table Matcher __init__")
        self.conf = conf
        self.S_LIST = S_LIST
        self.W_LIST = W_LIST
        self.all_enum_columns = {}
        self.all_synonyms_columns = {}
        self.all_synonyms_db = {}
        self.match_found = False
        self.tab = None

    def enum_matcher(self):
        # TODO root word matching - ('get states where families purchased umbrella insurance')
        print("Table Matcher: Enum_matcher enter")

        T_LIST = self.W_LIST + self.S_LIST
        for tupl in T_LIST:
            if len(tupl) == 1 and (tupl[0].like_num or tupl[0].lemma_ == u'be'):
                continue

            t = list(tupl)
            t = [i.text.encode('utf-8') for i in t]
            sub_phrase_list = [t[m:n + 1] for m in range(0, len(t)) for n in range(m, len(t))]
            sub_phrase_list.sort(key=lambda x: len(x), reverse=True)

            for sub_phrase in sub_phrase_list:
                print("enum_matcher before join")
                phrase = ' '.join(map(bytes.decode, sub_phrase))
                print("enum_matcher after join")
                for k in self.all_enum_columns:
                    if any(s.lower() == phrase for s in self.all_enum_columns[k]):
                        print("Table Matcher: Enum_matcher returning 1st")
                        return k[0]
        print("Table Matcher: Enum_matcher returning 2nd")
        return False

    def select_clause_matcher(self, S_filtered):
        # TODO root word matching

        S_filtered = [x for x in S_filtered if x.pos_ == u'NOUN']

        col_matches = []
        for word in S_filtered:
            for k in self.all_synonyms_db:
                if any(s.lower() == word.lemma_ for s in self.all_synonyms_db[k]):
                    return k

            for k in self.all_synonyms_columns:
                if any(s.lower() == word.lemma_ for s in self.all_synonyms_columns[k]):
                    col_matches.append(k[0])

        if len(col_matches) == 1:
            return col_matches[0]
        else:
            return False

    def where_clause_matcher(self, W_filtered):
        col_matches = []
        for word in W_filtered:
            for k in self.all_synonyms_columns:
                if any(s.lower() == word.lemma_ for s in self.all_synonyms_columns[k]):
                    col_matches.append(k[0])

        if len(col_matches) == 1:
            return col_matches[0]
        else:
            return False

    def table_extractor(self):
        print("Table Matcher table_extractor enter")
        # conf = config()
        load_metadata = self.conf.load_metadata

        if load_metadata:
            for db_name in self.conf.databases:
                filename = self.conf.metadata_base + db_name + '_metadata.pkl'
                with open(filename, 'rb') as f:
                    #md = pickle.load(f, fix_imports=True, encoding='bytes')
                    md = pickle.load(f)
                    print("Table Extractor Pickle load complete")
                    self.all_enum_columns.update(md[1])
                    self.all_synonyms_columns.update(md[2])

                    idx = self.conf.databases.index(db_name)
                    self.all_synonyms_db[self.conf.tables[idx]] = md[3]

        else:
            for i in range(len(self.conf.databases)):
                db = DbUtil(self.conf.connect_str.format(self.conf.databases[i]), self.conf.tables[i], self.conf)
                db.build_metadata(self.conf.db_synonyms[self.conf.databases[i]])
                self.all_enum_columns.update(db.enum_columns)
                self.all_synonyms_columns.update(db.synonyms)

                self.all_synonyms_db[self.conf.databases[i]] = db.db_synonyms

        print("Table Matcher: Metadata loaded")
        tab = self.enum_matcher()
        match_found = bool(tab)

        if not match_found:
            W_filtered = []
            for tupl in self.W_LIST:
                for w in list(tupl):
                    # W_filtered.append(WordNetLemmatizer().lemmatize(w.text,wordnet_pos(w.pos_)))
                    W_filtered.append(w)
            W_filtered = filter(lambda x: is_filter_word(x), W_filtered)

            tab = self.where_clause_matcher(W_filtered)
            match_found = bool(tab)

        if not match_found:
            S_filtered = []
            assert (len(self.S_LIST) == 1)
            for w in list(self.S_LIST[0]):
                # S_filtered.append(WordNetLemmatizer().lemmatize(w.text,wordnet_pos(w.pos_)))
                S_filtered.append(w)
            S_filtered = filter(lambda x: is_filter_word(x), S_filtered)

            tab = self.select_clause_matcher(S_filtered)
            match_found = bool(tab)

        if not match_found:
            # Word2Vec
            # TODO improve - take out stop words from db word list
            # similarity btwn bag of words, tf-idf, lucene etc
            print('>> Table Matching using word2vec ...')
            # import spacy
            # model = spacy.load('en')

            db_words_list = [[]] * len(self.conf.databases)
            # print db_words_list
            for k in self.all_synonyms_columns:
                idx = self.conf.tables.index(k[0])
                db_words_list[idx] = db_words_list[idx] + self.all_synonyms_columns[k]

            for k in self.all_synonyms_db:
                idx = self.conf.tables.index(k)
                db_words_list[idx] = db_words_list[idx] + self.all_synonyms_db[k]

            query_words_list = S_filtered + W_filtered
            query_words_str = ' '.join([i.text for i in query_words_list])
            query_doc = self.conf.nlp(query_words_str)
            max_sim = 0.0
            max_idx = None

            for i in range(len(db_words_list)):
                doc = self.conf.nlp(' '.join(db_words_list[i]))
                sim = doc.similarity(query_doc)
                if sim > max_sim:
                    max_sim = sim
                    max_idx = i

            tab = self.conf.tables[max_idx]

        print('>>TABLE>>', tab)
        return tab
