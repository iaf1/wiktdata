from itertools import zip_longest
from logger import autolog, clearlog


from wiktparser import WiktionaryParser
from wiktutils import Word

clearlog()

RAISE = 1


def default():

    try:
        mother_parser = WiktionaryParser()
        pit_parser = WiktionaryParser()
        beam_parser = WiktionaryParser()
        read_parser = WiktionaryParser()

        autolog('FETCHING "MOTHER"', 3)
        mother_word = mother_parser.fetch('mother', None, 0)

        autolog('FETCHING "PIT"', 3)
        pit_word = pit_parser.fetch('pit', None, 0)

        autolog('FETCHING "BEAM"', 3)
        beam_word = beam_parser.fetch('beam', None, 0)

        autolog('FETCHING "READ"', 3)
        read_word = read_parser.fetch('read', None, 0)

        mother = mother_parser.DEBUG
        pit = pit_parser.DEBUG
        beam = beam_parser.DEBUG
        read = read_parser.DEBUG

        return { 'mother_parser': mother_parser,
                 'pit_parser' : pit_parser,
                 'beam_parser' : beam_parser,
                 'read_parser' : read_parser,
                 'mother_word': mother_word,
                 'pit_word' : pit_word,
                 'beam_word' : beam_word,
                 'read_word' : read_word,
                 'mother' : mother,
                 'pit' : pit,
                 'beam' : beam,
                 'read' : read,
               }

    except:
        if RAISE: raise Exception


def custom(word):
    try:

        parser = WiktionaryParser()
        autolog('FETCHING CUSTOM WORD: {}'.format(word), 3)
        word = parser.fetch(word, None, 0)
        debug = parser.DEBUG

        return parser, word, debug

    except:
        if RAISE: raise Exception



def repr0(wd):
    etym = wd['etymologies']
    pron = wd['pronunciations']
    defs = wd['definitions']
    trns = wd['translations']

    for (cur, nxt) in zip_longest(etym, etym[1:], fillvalue=('','')):
        print('LOOP 1:', cur, nxt)
        for pin, ptx, audio in pron:
            print('\tLOOP 1.1:', pin, ptx, audio)
            print('\tCOMPARING:', cur[0], pin, nxt[0])
            if (pit_parser.count_digits(cur[0]) == pit_parser.count_digits(pin)) or (cur[0] <= pin < nxt[0]):
                print('\tIn if #1')
        for din, dtx, dty in defs:
            print('\tLOOP 1.2:', din, '(list)', dty)
            print('\tCOMPARING:', cur[0], din, nxt[0])
            if cur[0] <= din < nxt[0]:
                print('\tIn if #2')
            for tin, tdc in trns:
                print('\t\tLOOP 1.2.1:', tin, '(dict)')
                print('\t\tCOMPARING:', tin, din)
                if tin.startswith(".".join(din.split(".", 3)[:3])):
                    print('\t\tIn if #3')

