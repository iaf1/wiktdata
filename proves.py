#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 27 15:51:38 2020

@author: ivan
"""
from wiktparser import WiktionaryParser
from wiktutils import Word

parser = WiktionaryParser()

user_inp = input('Input word to search:\n>')

retrieved = parser.fetch(user_inp,'english')
#word_contents = parser.get_word_contents('english')
#tr = parser.parse_translations(wc, 0)
#wdo = parser.map_to_object(retrieved)

word = Word(retrieved, user_inp)
word.translation('russian')