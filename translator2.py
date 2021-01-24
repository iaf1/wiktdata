#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 18:21:02 2020

@author: ivan
"""

from wiktparser import WiktionaryParser
from wiktutils import Word

BREAK = ['q']

parser = WiktionaryParser()

lang_source = input("Input source language\n> ")

while True:

    inp_word = input('Input word:\n> ')
    if inp_word in BREAK: break

    print('{}: "{}" translator'.format(lang_source, inp_word))

    lang_target = ""

    while True:
        lang_target = input("Input target language\n> ")
        if lang_target in BREAK: break

        word = parser.fetch(inp_word ,lang_source, True)
        word.translation(lang_target)


# TODO: Investigate why word 'bishop' (eng to rus) gives error!!!!!!
# TODO: Fix main when there is main and sub (ex. eng to fr, "angry")
