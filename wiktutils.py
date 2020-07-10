from dicts import *

class WordData(object):
    def __init__(self, etymology=None, definitions=None, pronunciations=None,
                 audio_links=None):
        self.etymology = etymology if etymology else ''
        self.definition_list = definitions
        self.pronunciations = pronunciations if pronunciations else []
        self.audio_links = audio_links if audio_links else []

    @property
    def definition_list(self):
        return self._definition_list

    @definition_list.setter
    def definition_list(self, definitions):
        if definitions is None:
            self._definition_list = []
            return
        elif not isinstance(definitions, list):
            raise TypeError('Invalid type for definition')
        else:
            for element in definitions:
                if not isinstance(element, Definition):
                    raise TypeError('Invalid type for definition')
            self._definition_list = definitions

    def to_json(self):
        return {
            'etymology': self.etymology,
            'definitions': [definition.to_json() for definition in self._definition_list],
            'pronunciations': {
                'text': self.pronunciations,
                'audio': self.audio_links
            }
        }


class Definition(object):
    def __init__(self, part_of_speech = None, text = None, related_words = None, example_uses = None, translations = None):
        self.part_of_speech = part_of_speech if part_of_speech else ''
        self.text = text if text else ''
        self.related_words = related_words if related_words else []
        self.example_uses = example_uses if example_uses else []
        self.translations = translations if translations else []

    @property
    def related_words(self):
        return self._related_words

    @related_words.setter
    def related_words(self, related_words):
        if related_words is None:
            self._related_words = []
            return
        elif not isinstance(related_words, list):
            raise TypeError('Invalid type for relatedWord')
        else:
            for element in related_words:
                if not isinstance(element, RelatedWord):
                    raise TypeError('Invalid type for relatedWord')
            self._related_words = related_words

    def to_json(self):
        return {
            'partOfSpeech': self.part_of_speech,
            'text': self.text,
            'relatedWords': [related_word.to_json() for related_word in self.related_words],
            'examples': self.example_uses,
            'translations': self.translations
        }


class RelatedWord(object):
    def __init__(self, relationship_type=None, words=None):
        self.relationship_type = relationship_type if relationship_type else ''
        self.words = words if words else []

    def to_json(self):
        return {
            'relationshipType': self.relationship_type,
            'words': self.words
        }


class Word:
    def __init__(self,data,name=None):
        self.data = data
        self.name = name
        self.structure = [['{}'.format(PARTS_OF_SPEECH_DICT[elll.get('partOfSpeech')]) for elll in ell] for ell in [el.get('definitions') for el in self.data]]
        self._pronunciation = [el.get('pronunciations').get('text') for el in self.data]
        self._etymology = [el.get('etimology') for el in self.data]
        self._meaning = [['({}) {}'.format(PARTS_OF_SPEECH_DICT[elll.get('partOfSpeech')], '\n'.join(elll.get('text'))) for elll in ell] for ell in [el.get('definitions') for el in self.data]]
        self._meaning0 = [['{}'.format('\n'.join(elll.get('text'))) for elll in ell] for ell in [el.get('definitions') for el in self.data]]
        self._translation_lst = {}
        self._translation_txt = {}
        self.items = []
        for el in self.data:
            for el2 in el.get('definitions'):
                pofs = PARTS_OF_SPEECH_DICT[el2.get('partOfSpeech')]
                trns = el2.get('translations')
                for el3 in trns:
                    sense = el3[0]
                    langs_dict = el3[1]
                    self.items.append(list(langs_dict.items()))
                    for k, v in langs_dict.items():
                        if isinstance(v, dict):
                            for kk, vv in v.items():
                                dialect = k+'-'+kk.replace(k+' ','').replace(' '+k,'')
                                self._translation_lst[dialect] = self._translation_lst.get(dialect, {})
                                self._translation_lst[dialect]['{} ({})'.format(sense, pofs)] = ', '.join(vv) if isinstance(vv, list) else vv
                                self._translation_txt[dialect] = self._translation_txt.get(dialect, '')
                                self._translation_txt[dialect] += '\n({}) {}: {}'.format(pofs, sense, ', '.join(vv) if isinstance(vv, list) else vv)
                        else:
                            self._translation_lst[k] = self._translation_lst.get(k, {})
                            self._translation_lst[k]['{} ({})'.format(sense, pofs)] = ', '.join(v) if isinstance(v, list) else v
                            self._translation_txt[k] = self._translation_txt.get(k, '')
                            self._translation_txt[k] += '\n({}) {}: {}'.format(pofs, sense, ', '.join(v) if isinstance(v, list) else v)
        for k in self._translation_txt:
            self._translation_txt[k] = self._translation_txt[k].replace('\n','',1)+'\n'
        self._languages = sorted(list(self._translation_txt.keys()))

    
    def pronunciation(self):
        raise NotImplemented
                
    def meaning(self):
        raise NotImplemented
        
    def translation(self,*args):
        if args == ():
            args = self._languages
        for arg in args:
            for lang in self._languages:
                if lang.startswith(arg):
                    print('\t>>',lang)
                    print(self._translation_txt.get(lang), flush=True)
            
            
        