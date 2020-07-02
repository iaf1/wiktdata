#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 27 15:51:38 2020

@author: ivan
"""
from wiktparser import WiktionaryParser

parser = WiktionaryParser()

#ww = parser.fetch('mother','english')
ww = parser.fetch('mother','english')
wc = parser.get_word_contents('english')
tr = parser.parse_translations(wc, 1)

ww2 = parser.fetch('new','english')
wc = parser.get_word_contents('english')
tr2 = parser.parse_translations(wc, 1)