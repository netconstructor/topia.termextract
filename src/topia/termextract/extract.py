##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Term Extractor

$Id: extract.py 100557 2009-05-30 15:48:36Z srichter $
"""
import zope.interface

from topia.termextract import interfaces, tag

SEARCH = 0
NOUN = 1

def permissiveFilter(word, occur, strength):
    return True

class DefaultFilter(object):

    def __init__(self, singleStrengthMinOccur=3, noLimitStrength=2):
        self.singleStrengthMinOccur = singleStrengthMinOccur
        self.noLimitStrength = noLimitStrength

    def __call__(self, word, occur, strength):
        return ((strength == 1 and occur >= self.singleStrengthMinOccur) or
                (strength >= self.noLimitStrength))

def _add(term, norm, split, multiterm, terms):
    multiterm.append((term, norm, split))
    terms.setdefault(norm, 0)
    terms[norm] += 1

class TermExtractor(object):
    zope.interface.implements(interfaces.ITermExtractor)

    def __init__(self, tagger=None, filter=None):
        if tagger is None:
            tagger = tag.Tagger()
            tagger.initialize()
        self.tagger = tagger
        if filter is None:
            filter = DefaultFilter()
        self.filter = filter

    def extract(self, taggedTerms, splits, KEEP_ORIGINAL_SPACING):
        """See interfaces.ITermExtractor"""
        terms = {}
        # Phase 1: A little state machine is used to build simple and
        # composite terms.
        multiterm = []
        state = SEARCH
        assert len(taggedTerms) == len(splits)
        while taggedTerms:
            term, tag, norm = taggedTerms.pop(0)
            split = splits.pop(0)
            if state == SEARCH and tag.startswith('N'):
                state = NOUN
                _add(term, norm, split, multiterm, terms)
            elif state == SEARCH and tag == 'JJ' and term[0].isupper():
                state = NOUN
                _add(term, norm, split, multiterm, terms)
            elif state == NOUN and tag.startswith('N'):
                _add(term, norm, split, multiterm, terms)
            elif state == NOUN and not tag.startswith('N'):
                state = SEARCH
                if len(multiterm) > 1:
                    if KEEP_ORIGINAL_SPACING:
                        wholeword = ""
                        for i in range(len(multiterm)):
                            word, norm, split = multiterm[i]
                            wholeword += word
                            if split and i != len(multiterm)-1: wholeword += " "
                        word = wholeword
#                        if word != ' '.join([w for w, norm, split in multiterm]): print repr(word), repr(' '.join([w for w, norm, split in multiterm]))
#                        if word != ' '.join([w for w, norm, split in multiterm]): print "%40s %40s" % (word.encode("utf-8"), (' '.join([w for w, norm, split in multiterm])).encode("utf-8"))
                    else:
                        word = ' '.join([word for word, norm in multiterm])
                    terms.setdefault(word, 0)
                    terms[word] += 1
                multiterm = []
        # Phase 2: Only select the terms that fulfill the filter criteria.
        # Also create the term strength.
        return [
            (word, occur, len(word.split()))
            for word, occur in terms.items()
            if self.filter(word, occur, len(word.split()))]

    def __call__(self, text, KEEP_ORIGINAL_SPACING=True):
        """See interfaces.ITermExtractor"""
        split, terms = self.tagger(text)
        return self.extract(terms, split, KEEP_ORIGINAL_SPACING)

    def __repr__(self):
        return '<%s using %r>' %(self.__class__.__name__, self.tagger)
