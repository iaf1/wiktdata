#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 18:21:02 2020

@author: ivan
"""

from wiktparser import WiktionaryParser
from wiktutils import Word

parser = WiktionaryParser()

lang_source = input("Input source language\n> ")
lang_target = input("Input target language\n> ")

print('{} → {} translator.\n(Input "q" to quit)'.format(lang_source, lang_target))

inp = ""

while True:
    inp = input('Input word:\n> ')
    if inp in ['q']: break

    word = parser.fetch(inp,lang_source,True)
    word.translation(lang_target)