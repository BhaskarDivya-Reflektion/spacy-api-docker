import re
from nltk.parse.stanford import StanfordParser


class question_handler():
    def __init__(self, conf, query_text):
        self.conf = conf
        self.stanford_parser_loc = self.conf.stanford_parser_home + 'stanford-parser.jar'
        self.stanford_parser_model_loc = self.conf.stanford_parser_home + 'stanford-parser-3.9.2-models.jar'
        self.parse_model = StanfordParser(self.stanford_parser_loc, self.stanford_parser_model_loc,
                                          model_path="edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz")
        self.query_text = query_text

    def question_phrase_extract(self):
        # Get the 'question phrase' for example:
        # 'How many' in How many movies in 2016 , 'What actors' from What actors where born in 2014

        # How: 1. get lowest level Wh phrase - exceptions are internal 'who'
        # 2. first child .. travers up to first Wh phrse - rare exceptions where first word isn't WP

        if '?' not in self.query_text:
            self.query_text = self.query_text + '?'

        it = self.parse_model.raw_parse(self.query_text)
        tree = [i for i in it]
        t = tree[0][0]

        wh_tags = [u'WHPP', u'WHNP', u'WHADJP', u'WHADVP']

        p = t.leaf_treeposition(0)
        assert (t[p[:-1]].label() in [u'WDT', u'WP', u'WRB'] + wh_tags)

        while len(p) > 0:
            p = p[:-1]
            if '+' not in t[p].label():
                if t[p].label() in wh_tags:
                    wh_type = t[p].label()
                    wh_position = p
                    break
            else:
                print
                "+ in label!!"

        all_leaves_positions = []
        for i in range(len(t.leaves())):
            all_leaves_positions.append(t.leaf_treeposition(i))

        wh_leaves_positions1 = wh_position + t[wh_position].leaf_treeposition(0)
        wh_leaves_positions2 = wh_position + t[wh_position].leaf_treeposition(len(t[wh_position].leaves()) - 1)

        # print wh_leaves_positions1, wh_leaves_positions2
        absolute_position1 = all_leaves_positions.index(wh_leaves_positions1)
        absolute_position2 = all_leaves_positions.index(wh_leaves_positions2)

        # print absolute_position1, absolute_position2, wh_type
        return absolute_position1, absolute_position2, wh_type

    def is_question(self, spacy_doc):
        if spacy_doc[0].tag_ in [u'WDT', u'WP', u'WRB']:
            return True

        it = self.parse_model.raw_parse(self.query_text)
        tree = [i for i in it]
        root = tree[0][0]
        root_label = root.label()
        if root_label in [u'SBARQ', u'SQ']:
            return True
        elif u'SBAR' in root_label:
            # TODO incorrect logic - 'who' coming in between
            nodes = [root]
            while type(nodes[0]) == type(root):
                label_str = ' '.join([n.label() for n in nodes])
                if u'WHADJP' in label_str or u'WHNP' in label_str or u'WHPP' in label_str:
                    return True
                level_nodes = []
                for n in nodes:
                    for i in n:
                        level_nodes.append(i)
                nodes = level_nodes
            return False
        else:
            return False


class preprocessor():
    def __init__(self, conf, query_text):
        self.conf = conf
        self.query_text = query_text

    def spell_check(self):
        print("spell_check enter")
        from .spell_check import spell
        words = re.findall(r"[A-Za-z]+|[\d.,\d]+", self.query_text)

        if words[-1] == '.':
            words = words[:-1]

        print("spell_check before doc init")
        # import spacy
        # nlp = spacy.load("en")
        doc = self.conf.nlp(" ".join(words), disable=['parser'])
        print("spell_check after doc init")
        sp = spell()
        for i in range(len(words)):
            if doc[i].tag_ in [u'WDT', u'WP', u'WRB']:
                print("spell_check before correction1 call %s" % words[i].lower())
                words[i] = sp.correction(words[i].lower())
                words[i] = words[i].title()
                print("spell_check after correction1 call %s" % words[i].lower())
            elif doc[i].tag_ != u'NNP' and doc[i].tag_ != u'CD':
                print("spell_check before correction1 call %s" % words[i].lower())
                words[i] = sp.correction(words[i].lower())
                print("spell_check after correction1 call %s" % words[i].lower())

        print("spell_check after loop")
        self.query_text = " ".join(words)

    def replace_verb(self):
        words = self.query_text.split()
        doc = self.conf.nlp(self.query_text)

        if words[0].lower() in self.conf.select_words:
            for c in doc[0].children:
                if c.dep_ == u'dative' or c.dep_ == u'prep':
                    words.pop(c.i)
            words.pop(0)

            if words[0].lower() in [u'me', u'us', u'of']:
                words.pop(0)

            if words[0].lower() in [u'the']:
                words.pop(0)

            return " ".join(words)

        elif doc[0].pos_ in [u'NOUN', u'PROPN', u'ADJ']:
            return self.query_text
        else:
            return False

    def replace_operators(self):
        all_operators = self.conf.operator_high_words + self.conf.operator_low_words + self.conf.operator_equal_words + self.conf.group_words
        for o in all_operators:
            if o in self.query_text.lower():
                to_replace = re.compile(re.escape(o), re.IGNORECASE)
                if o in self.conf.operator_high_words:
                    self.query_text = to_replace.sub('more than', self.query_text)
                # return
                elif o in self.conf.operator_low_words:
                    self.query_text = to_replace.sub('less than', self.query_text)
                # return
                elif o in self.conf.operator_equal_words:
                    self.query_text = to_replace.sub('is', self.query_text)
                # return
                elif o in self.conf.group_words:
                    self.query_text = to_replace.sub('per', self.query_text)
                    # return

    def handle_order_by(self, ip_query_text):
        W_LIST = []
        doc = self.conf.nlp(ip_query_text)
        words = ip_query_text.split()
        idx = 0
        predef_words = self.conf.nlp(u'limit desc asc order 1')

        if doc[0].text == 'top' and doc[1].tag_ == u'CD':
            W_LIST.append((predef_words[0], doc[1]))
            words = words[2:]
            idx = 2

        # this assumes that if the query starts with top N ,
        # it has to be followed by JJS (superlative adjective)
        if doc[idx].tag_ == u'JJS':
            if idx != 2:
                W_LIST.append((predef_words[0], predef_words[4]))

            if doc[idx].text in [u'lowest', u'least']:
                W_LIST.append((predef_words[2],))
                words = words[1:]
                idx += 1
            elif doc[idx].text in [u'highest', u'most']:
                words = words[1:]
                idx += 1

            W_LIST.append((predef_words[3], doc[idx]))
            words = words[1:]

        return W_LIST, " ".join(words)


class value_extractor():
    def __init__(self, conf, query_text):
        self.conf = conf
        self.query_text = query_text
        self.S_LIST = []
        self.W_LIST = []

    def object_finder(self, node, is_visited):
        stack = []
        doc = node.doc
        stack.append(node)
        while len(stack) > 0:
            node = stack.pop()
            for c in node.children:
                if is_visited[c.i] == False and c.ent_type_ == 'DATE':
                    # i += (node.ent_iob-2)
                    tup = ()
                    i = c.i
                    # print i, '--', c.ent_iob ,'--', c.ent_type_, c.text
                    while i < len(doc) and doc[i].ent_type_ == 'DATE' and doc[i].text != u'per':
                        if c.ent_iob == 3:
                            tup = tup + (doc[i],)
                        elif c.ent_iob == 1:
                            tup = (doc[i],) + tup
                        is_visited[i] = True
                        i += (c.ent_iob - 2)
                    # self.W_LIST.append(tup)
                    if node.text.lower() in self.conf.time_words + self.conf.group_words:
                        self.W_LIST.append((node,) + tup)
                    else:
                        self.W_LIST.append(tup)

                    stack.append(c)

                # list of relation which should be added the the keyword-list directly
                # these tuples whould be modified later - to create the complete tuple
                elif u'obj' in c.dep_ or c.dep_ == u'npadvmod' or c.dep_ in [u'acl', u'advcl',
                                                                             u'relcl'] or c.dep_ == u'attr' or c.dep_ == u'neg':
                    if is_visited[c.i] == False:
                        stack.append(c)
                        if node.text.lower() in self.conf.time_words + self.conf.group_words:
                            self.W_LIST.append((node, c))
                        # is_visited[node.i] = True
                        else:
                            self.W_LIST.append((c,))

                # If the node -to- child has a compund relation then add it to the same tuple
                # for eg: [ Tom <---compound--- Cruise ] resulting tuple would be (Tom, Cruise)
                elif is_visited[c.i] == False and c.dep_ == u'compound':
                    phrase = (c, node)
                    next_children = [i for i in c.children]
                    while len(next_children) == 1 and next_children[0].dep_ == u'compound':
                        phrase = (next_children[0],) + phrase
                        next_children = [i for i in next_children[0].children]

                    idx = None
                    for tupl in self.W_LIST:
                        if node in tupl:
                            i = tupl.index(node)
                            left = tupl[0:i]
                            right = tupl[i + 1:]
                            idx = self.W_LIST.index(tupl)
                            break

                    if idx == None:
                        self.W_LIST.append(phrase)
                    else:
                        self.W_LIST[idx] = left + phrase + right

                # usually number words ('23','thirty') -- but in a lot of cases not handled
                # so add the 'number like' words to the keyword_list
                elif c.tag_ == u'CD' or c.like_num:
                    if is_visited[c.i] == False:
                        stack.append(c)
                        self.W_LIST.append((c,))

                # don't add preposition into W_List, but it would be added to the stack -- to get more keywords
                elif c.dep_ == u'prep' or c.dep_ == u'agent':
                    if is_visited[c.i] == False:
                        stack.append(c)

                # similar to the 'compound' rule , amod is basically an adjective , add to the same tupl
                # ex: [ male <--amod-- users ] , after this block (user,) will be changed to (male,users)
                elif c.dep_ == u'amod':
                    idx = None
                    for tupl in self.W_LIST:
                        if node in tupl:
                            # print ' -- -- ', tupl, node
                            i = tupl.index(node)
                            left = tupl[0:i]
                            right = tupl[i:]
                            idx = self.W_LIST.index(tupl)
                            break

                    if idx == None:
                        self.W_LIST.append((c, node))
                    else:
                        self.W_LIST[idx] = left + (c,) + right

                # similar to the first if block
                elif c.dep_ == u'ccomp' or c.dep_ == u'conj' or c.dep_ == u'pcomp':
                    if is_visited[c.i] == False:
                        stack.append(c)
                        self.W_LIST.append((c,))

                        # The next 2 rules deal with the subj relation - bothways
                        # ex: A <--subj-- B  &. A --subj--> B , 'B' both these cases should be a keyword

                elif node.pos_ == u'VERB' and u'subj' in c.dep_ and u'NN' in c.tag_:
                    if is_visited[c.i] == False:
                        stack.append(c)
                        self.W_LIST.append((c,))

            if (u'subj' in node.dep_ or u'acomp' in node.dep_) and node.head.pos_ == u'VERB':
                if is_visited[node.head.i] == False:
                    stack.append(node.head)
                    self.W_LIST.append((node.head,))

            is_visited[node.i] = True

        return is_visited

    def filter_W_LIST(self):
        filtered = set()
        for x in self.W_LIST:
            if len(x) == 1:
                if x[0].tag_ in [u'WDT', u'WP', u'WRB']:
                    filtered.add(x)
                if x[0].lemma_ in [u'be', u'do', u'have']:
                    filtered.add(x)
            if len(x) == 0:
                filtered.add(x)

        self.W_LIST = [x for x in self.W_LIST if x not in filtered]

    # return self.W_LIST

    def keyword_finder(self):
        print("keyword_finder enter")
        # not converting to lower - helps pos tagging
        preproc = preprocessor(self.conf, self.query_text)

        print("keyword_finder before spell_check")
        preproc.spell_check()
        print("keyword_finder after spell_check")

        print("keyword_finder before replace_operators")
        preproc.replace_operators()
        print("keyword_finder after replace_operators")

        print("keyword_finder before nlp init")
        self.query_text = preproc.query_text
        doc = self.conf.nlp(self.query_text)

        print("keyword_finder before question_handler")
        qh = question_handler(self.conf, self.query_text)
        question_check = qh.is_question(doc)

        print("keyword_finder before if not question_check")
        if not question_check:
            self.query_text = preproc.replace_verb()
            if not self.query_text:
                print
                "Use correct verb or question to phrase query!"
                return

            qt = self.query_text
            self.W_LIST, self.query_text = preproc.handle_order_by(qt)

            print
            ">>", self.query_text
            doc = self.conf.nlp(self.query_text)
            subj = None
            for w in doc:
                print
                w.head, w, w.dep_, w.tag_

            for w in doc:
                if w.dep_ == u'ROOT' and w.pos_ != u'VERB':
                    subj = w
                    self.S_LIST = [(subj,)]
                elif w.dep_ == u'ROOT' and w.pos_ == u'VERB':
                    for c in w.children:
                        if c.dep_ == u'nsubj':
                            subj = c
                            self.S_LIST = [(c,)]
                            break

            assert (subj != None)

            for child in subj.children:
                if child.dep_ == u'amod' or child.dep_ == u'compound':
                    phrase = (child, subj)
                    next_children = [i for i in child.children]
                    while len(next_children) == 1 and (
                                    next_children[0].dep_ == u'compound' or next_children[0].dep_ == u'amod'):
                        phrase = (next_children[0],) + phrase
                        next_children = [i for i in next_children[0].children]
                    self.S_LIST = [phrase]

            doc_len = len(doc)
            is_visited = [False] * doc_len

            is_visited = self.object_finder(subj, is_visited)

            self.filter_W_LIST()
            self.W_LIST = [x for x in self.W_LIST if x not in self.S_LIST]

        else:
            print
            ">>", self.query_text
            wh_position1, wh_position2, wh_type = qh.question_phrase_extract()
            wh_doc = doc[wh_position1:wh_position2 + 1]
            print
            wh_doc, wh_type
            for w in doc:
                print
                w.head, w, w.dep_, w.tag_

            if doc[0].text.lower() == u'who':
                subj = None
                for w in wh_doc:
                    if w.head not in wh_doc:
                        subj = w.head

                assert (subj != None)
                self.S_LIST.append((self.conf.nlp(u'person')[0],))
                self.W_LIST.append((subj,))

            elif wh_type == u'WHNP':
                subj = None
                for w in wh_doc:
                    if w.head not in wh_doc and w.head.pos_ == u'VERB' or w.head.pos_ == u'NOUN':
                        for c in w.head.children:
                            if u'subj' in c.dep_:  # or c.dep_ == u'attr':
                                subj = c
                                break
                            elif c not in wh_doc:
                                secondary_subj = c
                    elif len(wh_doc) == 1 and w.head not in wh_doc:
                        secondary_subj = w.head

                # if only one word .. then whatever is head  what <-- []
                if subj == None:
                    subj = secondary_subj
                assert (subj != None)

                self.S_LIST = [(subj,)]

                for child in subj.children:
                    if child.dep_ == u'amod' or child.dep_ == u'compound':
                        phrase = (child, subj)
                        next_children = [i for i in child.children]
                        while len(next_children) == 1 and (
                                        next_children[0].dep_ == u'compound' or next_children[0].dep_ == u'amod'):
                            phrase = (next_children[0],) + phrase
                            next_children = [i for i in next_children[0].children]
                        self.S_LIST = [phrase]


            elif wh_type == u'WHADJP':
                subj_child = None
                for w in wh_doc:
                    if w.head not in wh_doc and (w.dep_ == u'amod' or w.dep_ == u'advmod'):
                        subj_child = w
                    elif u'mod' in w.dep_:
                        # how <--advmod--many
                        secondary_subj = w.head

                if subj_child == None:
                    subj = secondary_subj
                    self.S_LIST.append((subj,))
                else:
                    subj = subj_child.head
                    self.S_LIST.append((subj_child, subj))

                assert (subj != None)

            elif wh_type == u'WHADVP' and doc[0].text.lower() == u'when':
                if doc[0].text.lower() == u'when':
                    subj = None
                    for w in wh_doc:
                        if w.head not in wh_doc:
                            subj = w.head

                    assert (subj != None)
                    self.S_LIST.append((self.conf.nlp(u'date')[0],))
                    self.W_LIST.append((subj,))

                else:
                    pass

            elif doc[0].text.lower() == u'where':
                subj = None
                for w in wh_doc:
                    if w.head not in wh_doc:
                        subj = w.head

                assert (subj != None)
                self.S_LIST.append((self.conf.nlp(u'location')[0],))
                self.W_LIST.append((subj,))

            doc_len = len(doc)
            is_visited = [False] * doc_len

            self.object_finder(subj, is_visited)

            self.filter_W_LIST()
            self.W_LIST = [x for x in self.W_LIST if x not in self.S_LIST]
        # TODO handle 'WHPP'

        print("keyword_finder before return")

        print
        '>>> S >> ', self.S_LIST
        print
        '>>> W >> ', self.W_LIST

        return self.S_LIST, self.W_LIST
