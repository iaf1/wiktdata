import re, requests
from wiktutils import WordData, Definition, RelatedWord
from bs4 import BeautifulSoup
from itertools import zip_longest
from copy import copy
from string import digits
from dicts import *
from logger import autolog

class WiktionaryParser(object):
    def __init__(self,language='english',url_preffix='en', verbose=False):
        autolog('CHECKIN')
        self.url_preffix = url_preffix.lower()
        self.url = "https://{}.wiktionary.org/wiki/{}?printable=yes"
        self.soup = None
        self.session = requests.Session()
        self.session.mount("http://", requests.adapters.HTTPAdapter(max_retries = 2))
        self.session.mount("https://", requests.adapters.HTTPAdapter(max_retries = 2))
        self.language = language.lower()
        self.current_word = None
        self.PARTS_OF_SPEECH = copy(PARTS_OF_SPEECH)
        self.RELATIONS = copy(RELATIONS)
        self.INCLUDED_ITEMS = self.RELATIONS + self.PARTS_OF_SPEECH + ['etymology', 'pronunciation','translations']
        
        self.verbose = verbose
        
        self._transl_tag = []
        self.item0 = []

        self.DEBUG = {}
        autolog('CHECKOUT')

    def include_part_of_speech(self, part_of_speech):
        autolog('CHECKIN')
        part_of_speech = part_of_speech.lower()
        if part_of_speech not in self.PARTS_OF_SPEECH:
            self.PARTS_OF_SPEECH.append(part_of_speech)
            self.INCLUDED_ITEMS.append(part_of_speech)
        autolog('CHECKOUT')

    def exclude_part_of_speech(self, part_of_speech):
        part_of_speech = part_of_speech.lower()
        self.PARTS_OF_SPEECH.remove(part_of_speech)
        self.INCLUDED_ITEMS.remove(part_of_speech)
        autolog('CHECKOUT')

    def include_relation(self, relation):
        autolog('CHECKIN')
        relation = relation.lower()
        if relation not in self.RELATIONS:
            self.RELATIONS.append(relation)
            self.INCLUDED_ITEMS.append(relation)
        autolog('CHECKOUT')

    def exclude_relation(self, relation):
        autolog('CHECKIN')
        relation = relation.lower()
        self.RELATIONS.remove(relation)
        self.INCLUDED_ITEMS.remove(relation)
        autolog('CHECKOUT')

    def set_default_language(self, language=None):
        autolog('CHECKIN')
        if language is not None:
            self.language = language.lower()
        autolog('CHECKOUT')
    
    def set_url_preffix(self,url_preffix=None):
        autolog('CHECKIN')
        if url_preffix is not None:
            self.url_preffix = url_preffix.lower()
        autolog('CHECKOUT')

    def get_default_language(self):
        autolog('CHECKIN')
        return self.language
        autolog('CHECKOUT')
    
    def get_url_preffix(self):
        autolog('CHECKIN')
        return self.url_preffix

    def clean_html(self):
        autolog('CHECKIN')
        unwanted_classes = ['sister-wikipedia', 'thumb', 'reference', 'cited-source']
        for tag in self.soup.find_all(True, {'class': unwanted_classes}):
            tag.extract()
        autolog('CHECKOUT')

    def remove_digits(self, string):
        return string.translate(str.maketrans('', '', digits)).strip()

    def count_digits(self, string):
        return len(list(filter(str.isdigit, string)))

    def get_id_list(self, content_type=None):
        """Searches in word contents, with the aim of finding the section id of those
        sections whose content type matches the requested one.
        
        INPUT:
            content_type (str)

        OUTPUT:
            a list of tuples with the following format:
                (index, id, text_that_matched_criteria)

            Example 1: content_type: 'pronunciation'
                [('1.1', 'Pronunciation', 'pronunciation')]
                
            Example 2: content_type: 'definitions'
                [('1.2.1', 'Noun', 'noun'),
                ('1.2.3', 'Verb', 'verb'),
                ('1.3.1', 'Noun_2', 'noun')]
        """


        autolog('CHECKIN')
        soup = self.soup
        contents = self.word_contents

        # Define checklists, depending on the content_type
        if content_type == 'etymologies':
            checklist = ['etymology']
        elif content_type == 'pronunciation':
            checklist = ['pronunciation']
        elif content_type == 'definitions':
            checklist = self.PARTS_OF_SPEECH
            if self.language == 'chinese':
                checklist += self.current_word
        elif content_type == 'related':
            checklist = self.RELATIONS
        elif content_type == 'translations':
            checklist = ['translations']
        else:
            return None


        id_list = []
        if len(contents) == 0:
            return [('1', x.title(), x) for x in checklist if soup.find('span', {'id': x.title()})]

        # Add index, id and text for all those text that match the checklist
        for content_tag in contents:
            content_index = content_tag.find_previous().text
            text_to_check = self.remove_digits(content_tag.text).strip().lower()
            if text_to_check in checklist:
                content_id = content_tag.parent['href'].replace('#', '')
                id_list.append((content_index, content_id, text_to_check))
        autolog('CHECKOUT')
        autolog('IN: {} | OUT: {}'.format(content_type, id_list), 0)
        return id_list

    def get_word_contents(self, language):
        """Returns list of bs4.element.Tag whose text is in the recognized terms
        and in the appropriate language
        """

        autolog('CHECKIN')
        contents = self.soup.find_all('span', {'class': 'toctext'})
        word_contents = []
        start_index = None

        # First find language to define index
        for content in contents:
            if content.text.lower() == language:
                start_index = content.find_previous().text + '.'
        if len(contents) != 0 and not start_index:
            return []

        # Pick contents with appropiate index (thus language)
        for content in contents:
            index = content.find_previous().text
            content_text = self.remove_digits(content.text.lower())
            if index.startswith(start_index) and content_text in self.INCLUDED_ITEMS:
                word_contents.append(content)

        self.word_contents = word_contents
        self.DEBUG['word_contents'] = word_contents
        autolog(word_contents, 0)
        autolog('CHECKOUT')
        return word_contents

    def get_word_data(self):
        autolog('CHECKIN')
        word_data = {
            'examples': self.parse_examples(),
            'definitions': self.parse_definitions(),
            'etymologies': self.parse_etymologies(),
            'related': self.parse_related_words(),
            'pronunciations': self.parse_pronunciations(),
            'translations': self.parse_translations(),
        }
        #print(word_data['translations'])
        #return word_data
        self.DEBUG['word_data0'] = word_data
        json_obj_list = self.map_to_object(word_data)
        self.DEBUG['get_word_data'] = json_obj_list
        self.DEBUG['word_data'] = json_obj_list
        autolog('OUT: {}'.format('See DEBUG["get_word_data"]'), 2)
        autolog('CHECKOUT')
        return json_obj_list

    def parse_pronunciations(self):
        autolog('CHECKIN')
        word_contents = self.word_contents
        pronunciation_id_list = self.get_id_list('pronunciation')
        pronunciation_list = []
        audio_links = []
        pronunciation_text = []
        pronunciation_div_classes = ['mw-collapsible', 'vsSwitcher']
        for pronunciation_index, pronunciation_id, _ in pronunciation_id_list:
            span_tag = self.soup.find_all('span', {'id': pronunciation_id})[0]
            list_tag = span_tag.parent
            while list_tag.name != 'ul':
                list_tag = list_tag.find_next_sibling()
                if list_tag.name == 'p':
                    pronunciation_text.append(list_tag.text)
                    break
                if list_tag.name == 'div' and any(_ in pronunciation_div_classes for _ in list_tag['class']):
                    break
            for super_tag in list_tag.find_all('sup'):
                super_tag.clear()
            for list_element in list_tag.find_all('li'):
                for audio_tag in list_element.find_all('div', {'class': 'mediaContainer'}):
                    audio_links.append(audio_tag.find('source')['src'])
                    audio_tag.extract()
                for nested_list_element in list_element.find_all('ul'):
                    nested_list_element.extract()
                if list_element.text and not list_element.find('table', {'class': 'audiotable'}):
                    pronunciation_text.append(list_element.text.strip())
            pronunciation_list.append((pronunciation_index, pronunciation_text, audio_links))
        autolog('CHECKOUT')
        return pronunciation_list

    def parse_definitions(self):
        autolog('CHECKIN')
        word_contents = self.word_contents
        definition_id_list = self.get_id_list('definitions')
        definition_list = []
        definition_tag = None
        for def_index, def_id, def_type in definition_id_list:
            definition_text = []
            span_tag = self.soup.find_all('span', {'id': def_id})[0]
            table = span_tag.parent.find_next_sibling()
            while table and table.name not in ['h3', 'h4', 'h5']:
                definition_tag = table
                table = table.find_next_sibling()
                if definition_tag.name == 'p':
                    definition_text.append(definition_tag.text.strip())
                if definition_tag.name in ['ol', 'ul']:
                    for element in definition_tag.find_all('li', recursive=False):
                        if element.text:
                            definition_text.append(element.text.strip())
            if def_type == 'definitions':
                def_type = ''
            definition_list.append((def_index, definition_text, def_type))
        autolog('CHECKOUT')
        return definition_list

    def parse_examples(self):
        autolog('CHECKIN')
        word_contents = self.word_contents
        definition_id_list = self.get_id_list('definitions')
        example_list = []
        for def_index, def_id, def_type in definition_id_list:
            span_tag = self.soup.find_all('span', {'id': def_id})[0]
            table = span_tag.parent
            while table.name != 'ol':
                table = table.find_next_sibling()
            examples = []
            while table and table.name == 'ol':
                for element in table.find_all('dd'):
                    example_text = re.sub(r'\([^)]*\)', '', element.text.strip())
                    if example_text:
                        examples.append(example_text)
                    element.clear()
                example_list.append((def_index, examples, def_type))
                for quot_list in table.find_all(['ul', 'ol']):
                    quot_list.clear()
                table = table.find_next_sibling()
        autolog('CHECKOUT')
        return example_list

    def parse_etymologies(self):
        autolog('CHECKIN')
        word_contents = self.word_contents
        etymology_id_list = self.get_id_list('etymologies')
        etymology_list = []
        etymology_tag = None
        for etymology_index, etymology_id, _ in etymology_id_list:
            etymology_text = ''
            span_tag = self.soup.find_all('span', {'id': etymology_id})[0]
            next_tag = span_tag.parent.find_next_sibling()
            while next_tag.name not in ['h3', 'h4', 'div', 'h5']:
                etymology_tag = next_tag
                next_tag = next_tag.find_next_sibling()
                if etymology_tag.name == 'p':
                    etymology_text += etymology_tag.text
                else:
                    for list_tag in etymology_tag.find_all('li'):
                        etymology_text += list_tag.text + '\n'
            etymology_list.append((etymology_index, etymology_text))
        autolog('CHECKOUT')
        return etymology_list

    def parse_related_words(self):
        autolog('CHECKIN')
        word_contents = self.word_contents
        relation_id_list = self.get_id_list('related')
        related_words_list = []
        for related_index, related_id, relation_type in relation_id_list:
            words = []
            span_tag = self.soup.find_all('span', {'id': related_id})[0]
            parent_tag = span_tag.parent
            while not parent_tag.find_all('li'):
                parent_tag = parent_tag.find_next_sibling()
            for list_tag in parent_tag.find_all('li'):
                words.append(list_tag.text)
            related_words_list.append((related_index, words, relation_type))
        autolog('CHECKOUT')
        return related_words_list


    def extract_languages(self, sense_tag):
        autolog('CHECKIN')

        lang_tags = sense_tag.find_all('li')
        lang_dict = {}
        for lang_tag in lang_tags:
            if lang_tag.find_all('dl') == []:
                # There are no dialects (subitems in a language)
                lang_dict = dict(lang_dict, **self.extract_language_item(lang_tag))
            else:
                # There are dialects
                lang = lang_tag.text.split(':')[0]
                descriptions_dict = {}

                temp = copy(lang_tag)
                temp.find('dl').extract()

                if temp.text.replace('\n','').split(':')[1] != '':
                    # There is still a main entry
                    autolog('SENDING {}'.format(temp), 2)
                    descriptions_dict = dict(descriptions_dict, **self.extract_language_item(temp))

                for descr in lang_tag.find_all('dd'):
                    if descr.find_all('dl') == []:
                        autolog('LANG: {}, NOT dl: {}'.format(lang, descr), 0)
                        descriptions_dict = dict(descriptions_dict, **self.extract_language_item(descr))
                    else:
                        autolog('SPECIAL CASE. LANG: {}, YES dl: {}'.format(lang, descr), 2)
                        for descr2 in descr.find_all('dl'):
                            descriptions_dict = dict(descriptions_dict, **self.extract_language_item(descr2))
                            descr2.extract()
                        descriptions_dict = dict(descriptions_dict, **self.extract_language_item(descr))
                lang_dict[lang.lower()] = descriptions_dict
        
        if self.DEBUG.get('extract_languages') is None: self.DEBUG['extract_languages'] = lang_dict

        autolog('CHECKOUT')
        return lang_dict


    def extract_language_item(self, lang_tag):
        unwanted_classes = ['tpos']
        enclose_classes = ['gender']

        # Extract unwanted classes. Enclose genders
        for tag in lang_tag.find_all(True, {'class': unwanted_classes}):
            tag.extract()
        for tag in lang_tag.find_all(True, {'class': enclose_classes}):
            tag.replace_with('['+tag.text+']')

        # Take text, and separate: lang & translation (by colon)
        text = lang_tag.text
        try:
            key, items_text = text.split(': ',1)
            autolog(f'KEY: {key}\n\tITEMS_TEXT: {items_text}', 2)
        except:
            print(text)
            raise Exception("Impossible to extract language")

        # Separate different items (by commas)
        # Also, replace '[[a|b]]' for 'b' (gender notation)
        items_list = items_text.split(', ')
        for i in range(len(items_list)):
            item = items_list[i]
            if '[[' in item and ']]' in item and '|' in item:
                items_list[i] = item.split('|')[1].replace(']]','')

        # If all ',()' chars are in text, go through list so as to ignore , between ()
        if ',' in items_text and '(' in items_text and ')' in items_text:
            items_new = []
            cur_chain = []
            connecting = False
            counts = [0, 0]
            for el in items_list:
                counts[0] += el.count('(')
                counts[1] += el.count(')')
                cur_chain.append(el)
                if counts[0] == counts[1]:
                    items_new.append(', '.join(cur_chain))
                    cur_chain = []

            items_list = items_new

        # Return a dict whose value is the list or its only element
        return {key.lower() : items_list if len(items_list) > 1 else items_list[0]}

        
        
    def parse_translations(self):
        """Returns a structure of the kind:
        [
            ( index1, [
                        sense 1.1, {lang1: transl1, lang2: defs2, ... },
                        sense 1.2, {lang1: transl1, lang2: defs2, ... },
                        ...
                      ]
            ),
            ( index2, ...),
            ...
        ]
            """
        autolog('CHECKIN')
        word_contents = self.word_contents
        translations_id_list = self.get_id_list('translations')
        translations_list = []

        for translations_index, translations_id, _ in translations_id_list:

            cur_translation_list = []

            span_tag = self.soup.find_all('span', {'id': translations_id})[0]
            if self.DEBUG.get('transl1') is None: self.DEBUG['transl1'] = span_tag
            cur_transl_senses = self.get_senses(span_tag.parent.find_next_sibling())
            
            # If translations are somewhere else, go look for them
            if len(cur_transl_senses) == 1 and '/translations' in cur_transl_senses[0][1].text:
                autolog(cur_transl_senses, 2)
                url2 = cur_transl_senses[0][1].find('a').get('href').replace('/wiki/','')

                session2 = requests.Session()
                session2.mount("http://", requests.adapters.HTTPAdapter(max_retries = 2))
                session2.mount("https://", requests.adapters.HTTPAdapter(max_retries = 2))
                response = session2.get(self.url.format(self.url_preffix, url2))
                soup2 = BeautifulSoup(response.text, 'html.parser')
                span_tag = soup2.find('span',{'id':url2.split('#')[1]})
                self._soup2 = soup2

                if self.DEBUG.get('transl2') is None: self.DEBUG['transl2'] = span_tag

                cur_transl_senses = self.get_senses(span_tag.parent.find_next_sibling().find_next_sibling())

            for (sense, sense_tag) in cur_transl_senses:

                cur_translation_list.append((sense, self.extract_languages(sense_tag)))

                
            
            if self.DEBUG.get('cur_transl_list') is None: self.DEBUG['cur_transl_list'] = cur_translation_list
            
            translations_list.append((translations_index, cur_translation_list))
                
        autolog('translations_list: {}'.format(translations_list), 0)

        self.DEBUG['translations_list'] = translations_list
        self.DEBUG['parse_translations'] = translations_list

        autolog('CHECKOUT')
        return translations_list


    def get_senses(self, transl_tag):
        """Builds and returns a dictionary of translation siblings (bs4.element.Tag),
        i.e. one for each of the senses of a word.
        Output format:
            {
                (sense1, bs4.element.Tag with all the languages),
                (sense2, bs4.element.Tag with all the languages),
            }
        """
        autolog('CHECKIN')
        self.DEBUG['transl_tag'] = transl_tag

        sense_tag = transl_tag

        senses = []

        while True:
            # Check if the table of senses is over
            if sense_tag is None:
                break
            try:
                sense_tag_name = sense_tag.name
            except:
                break
            if sense_tag_name in ['h3','h4','h5']:
                break

            # get the sense name
            sense_header = sense_tag.find('div')
            if sense_header is None:
                sense = ''
            else:
                sense = sense_header.text

            # add to dictionary
            senses.append((sense, sense_tag))
            self.DEBUG['last_transl_tag'] = sense_tag
            sense_tag = sense_tag.find_next_sibling()
        
        autolog('CHECKOUT')
        return senses

    def map_to_object(self, word_data):
        autolog('CHECKIN')
        self.DEBUG['map_to_object_input'] = word_data
        json_obj_list = []
        if not word_data['etymologies']:
            word_data['etymologies'] = [('', '')]

        # Loop over etimologies
        for (current_etymology, next_etymology) in zip_longest(word_data['etymologies'], word_data['etymologies'][1:], fillvalue=('999', '')):
            data_obj = WordData()
            data_obj.etymology = current_etymology[1]

            # Loop over pronunciations
            # Check if:
            #   1. Pronunciation is at the same level of etymology(ies)
            #   2. Proununciation index "is sorted" after current etymology index
            #      and before next etymology index (string comparison)

            for pronunciation_index, pronunciation_text, audio_links in word_data['pronunciations']:
                if (self.count_digits(current_etymology[0]) == self.count_digits(pronunciation_index)) or (current_etymology[0] <= pronunciation_index < next_etymology[0]):
                    data_obj.pronunciations = pronunciation_text
                    data_obj.audio_links = audio_links

            # Loop over definitions
            # Check if definition index "sorts" after current etymology index
            # and before next etymology index (string comparison)
            # If so, loop over examples, related and translations, and for each one,
            # pick the ones whose index starts like the definition index

            for (current_definition, next_definition) in zip_longest(word_data['definitions'], word_data['definitions'][1:], fillvalue=('999', '', '')):
                definition_index, definition_text, definition_type = current_definition
                next_definition_index, _, _ = next_definition

                if current_etymology[0] <= definition_index < next_etymology[0]:
                    if self.verbose: print('\n>>', definition_index, definition_text)
                    def_obj = Definition()
                    def_obj.text = definition_text
                    def_obj.part_of_speech = definition_type
                    for example_index, examples, _ in word_data['examples']:
                        if example_index.startswith(definition_index):
                            def_obj.example_uses = examples
                    for related_word_index, related_words, relation_type in word_data['related']:
                        if related_word_index.startswith(definition_index):
                            def_obj.related_words.append(RelatedWord(relation_type, related_words))
                    found = False
                    for translations_index, translations_dict in word_data['translations']:
                        if definition_index <= translations_index < next_definition_index:
                            def_obj.translations = translations_dict
                            autolog('COND 1: {} {}'.format(translations_index, definition_index), 0)

                    data_obj.definition_list.append(def_obj)

            json_obj_list.append(data_obj.to_json())

        self.DEBUG['map_to_object'] = json_obj_list
        self.DEBUG['json_obj_list'] = json_obj_list
        autolog('OUT: See DEBUG["map_to_object"]', 0)
        autolog('CHECKOUT')

        return json_obj_list


    def fetch(self, word, language=None, wordclass=True):
        autolog('CHECKIN')
        language = language or self.language
        response = self.session.get(self.url.format(self.url_preffix, word))
        self.soup = BeautifulSoup(response.text.replace('>\n<', '><'), 'html.parser')
        self.current_word = word
        self.clean_html()
        self.get_word_contents(language)
        word_data = self.get_word_data()
        autolog('CHECKOUT')
        if not wordclass:
            return word_data
        else:
            from wiktutils import Word
            return Word(word_data, self.current_word)