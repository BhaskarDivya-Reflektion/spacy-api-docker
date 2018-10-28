import re
from collections import Counter


class spell(object):
    def __init__(self):
        self.WORDS = Counter(self.words(open('/app/displacy_service/eng2sql/words_list.txt').read()))
        self.N = sum(self.WORDS.values())
        print("Spell Check init done %s" % self.WORDS)

    def words(self, text):
        print("spell_Check words enter")
        ret = re.findall(r'\w+', text.lower())
        print("spell_Check words exit")
        return ret

    def P(self, word):
        "Probability of `word`."
        return self.WORDS[word] / self.N

    def correction(self, word):
        "Most probable spelling correction for word."
        print("spell_Check correction enter")
        ret = max(self.candidates(word), key=self.P)
        print("spell_Check correction exit")
        return ret

    def candidates(self, word):
        "Generate possible spelling corrections for word."
        print("spell_Check candidates enter")
        ret = (self.known([word]) or self.known(self.edits1(word)) or self.known(self.edits2(word)) or [word])
        print("spell_Check candidates exit")
        return ret

    def known(self, words):
        "The subset of `words` that appear in the dictionary of WORDS."
        print("spell_Check known enter")
        ret = set(w for w in words if w in self.WORDS)
        print("spell_Check known exit")
        return ret

    def edits1(self, word):
        "All edits that are one edit away from `word`."
        print("spell_Check edits1 enter")
        letters = 'abcdefghijklmnopqrstuvwxyz'
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts = [L + c + R for L, R in splits for c in letters]
        print("spell_Check edits1 exit")
        return set(deletes + transposes + replaces + inserts)

    def edits2(self, word):
        "All edits that are two edits away from `word`."
        print("spell_Check edits2 enter")
        return (e2 for e1 in self.edits1(word) for e2 in self.edits1(e1))

        # i = 0
        # for k in WORDS:
        #     #print k,
        #     if i%20==0:
        #         print '\n',
        #     i += 1
