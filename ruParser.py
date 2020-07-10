import re, requests
from wiktutils import WordData, Definition, RelatedWord
from bs4 import BeautifulSoup
from itertools import zip_longest
from copy import copy
from string import digits
from dicts import *

class RussianParser(object):
    def __init__(self,language='русский'):
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
        
        self._transl_tag = []
        self.item0 = []

    def include_part_of_speech(self, part_of_speech):
        part_of_speech = part_of_speech.lower()
        if part_of_speech not in self.PARTS_OF_SPEECH:
            self.PARTS_OF_SPEECH.append(part_of_speech)
            self.INCLUDED_ITEMS.append(part_of_speech)

    def exclude_part_of_speech(self, part_of_speech):
        part_of_speech = part_of_speech.lower()
        self.PARTS_OF_SPEECH.remove(part_of_speech)
        self.INCLUDED_ITEMS.remove(part_of_speech)        

    def include_relation(self, relation):
        relation = relation.lower()
        if relation not in self.RELATIONS:
            self.RELATIONS.append(relation)
            self.INCLUDED_ITEMS.append(relation)

    def exclude_relation(self, relation):
        relation = relation.lower()
        self.RELATIONS.remove(relation)
        self.INCLUDED_ITEMS.remove(relation)

    def set_default_language(self, language=None):
        if language is not None:
            self.language = language.lower()
    
    def set_url_preffix(self,url_preffix=None):
        if url_preffix is not None:
            self.url_preffix = url_preffix.lower()

    def get_default_language(self):
        return self.language
    
    def get_url_preffix(self):
        return self.url_preffix

    def clean_html(self):
        unwanted_classes = ['sister-wikipedia', 'thumb', 'reference', 'cited-source']
        for tag in self.soup.find_all(True, {'class': unwanted_classes}):
            tag.extract()

    def remove_digits(self, string):
        return string.translate(str.maketrans('', '', digits)).strip()

    def count_digits(self, string):
        return len(list(filter(str.isdigit, string)))

    def get_id_list(self, contents=None, content_type=None, soup=None):
        soup = soup or self.soup
        contents = contents or self.get_word_contents(self.language, soup)

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
        for content_tag in contents:
            content_index = content_tag.find_previous().text
            text_to_check = self.remove_digits(content_tag.text).strip().lower()
            if text_to_check in checklist:
                content_id = content_tag.parent['href'].replace('#', '')
                id_list.append((content_index, content_id, text_to_check))
        return id_list

    def get_word_contents(self, language, soup=None):
        soup = soup or self.soup
        contents = soup.find_all('span', {'class': 'toctext'})
        word_contents = []
        start_index = None
        for content in contents:
            if content.text.lower() == language:
                start_index = content.find_previous().text + '.'
        if len(contents) != 0 and not start_index:
            return []
        for content in contents:
            index = content.find_previous().text
            content_text = self.remove_digits(content.text.lower())
            if index.startswith(start_index) and content_text in self.INCLUDED_ITEMS:
                word_contents.append(content)
        if soup is None:
            self.word_contents = word_contents
        return word_contents

    def get_word_data(self, language, soup=None):
        word_contents = self.get_word_contents(language, soup)
        word_data = {
            'examples': self.parse_examples(word_contents),
            'definitions': self.parse_definitions(word_contents),
            'etymologies': self.parse_etymologies(word_contents),
            'related': self.parse_related_words(word_contents),
            'pronunciations': self.parse_pronunciations(word_contents),
            'translations': self.parse_translations(word_contents),
        }
        #print(word_data['translations'])
        #return word_data
        json_obj_list = self.map_to_object(word_data)
        return json_obj_list

    def parse_pronunciations(self, word_contents=None):
        word_contents = word_contents or self.word_contents
        pronunciation_id_list = self.get_id_list(word_contents, 'pronunciation')
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
        return pronunciation_list

    def parse_definitions(self, word_contents=None):
        word_contents = word_contents or self.word_contents
        definition_id_list = self.get_id_list(word_contents, 'definitions')
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
        return definition_list

    def parse_examples(self, word_contents):
        word_contents = word_contents or self.word_contents
        definition_id_list = self.get_id_list(word_contents, 'definitions')
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
        return example_list

    def parse_etymologies(self, word_contents=None):
        word_contents = word_contents or self.word_contents
        etymology_id_list = self.get_id_list(word_contents, 'etymologies')
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
        return etymology_list

    def parse_related_words(self, word_contents=None):
        word_contents = word_contents or self.word_contents
        relation_id_list = self.get_id_list(word_contents, 'related')
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
        return related_words_list

    def extract_languages(self,translation_contents):
        def extract_item(lang_tag):
            unwanted_classes = ['tpos']
            enclose_classes = ['gender']
            items_dict = {}
            for tag in lang_tag.find_all(True, {'class': unwanted_classes}):
                tag.extract()
            for tag in lang_tag.find_all(True, {'class': enclose_classes}):
                tag.replace_with('['+tag.text+']')
            text = lang_tag.text
            try:
                key, items_text = text.split(': ',1)
            except:
                print(text)
                raise Exception("Impossible to extract language")
            items_list = items_text.split(', ')
            for i in range(len(items_list)):
                item = items_list[i]
                if '[[' in item and ']]' in item and '|' in item:
                    items_list[i] = item.split('|')[1].replace(']]','')
            if ',' in items_text and '(' in items_text and ')' in items_text:
                items_new = []
                cur_chain = []
                connecting = False
                for el in items_list:
                    if '(' in el and not ')' in el:
                        connecting = True
                    elif ')' in el and not '(' in el:
                        connecting = False
                    cur_chain.append(el)
                    if connecting is False:
                        items_new.append(', '.join(cur_chain))
                        cur_chain = []
                items_list = items_new
                #print(items_list)
            items_dict[key.lower()] = items_list if len(items_list) > 1 else items_list[0]
            self.item0.append(items_dict)
            return items_dict
        
        translations = []
        for translation_content in translation_contents:
            try:
                sense = translation_content.find('div').text
            except:
                continue
            lang_tags = translation_content.find_all('li')
            lang_dict = {}
            for lang_tag in lang_tags:
                if lang_tag.find_all('dd') == []:
                    lang_dict = dict(lang_dict, **extract_item(lang_tag))
                else:
                    lang = lang_tag.text.split(':')[0]
                    descriptions_dict = {}
                    for descr in lang_tag.find_all('dd'):
                        if descr.find_all('dl') == []:
                            descriptions_dict = dict(descriptions_dict, **extract_item(descr))
                        else:
                            for descr2 in descr.find_all('dl'):
                                descriptions_dict = dict(descriptions_dict, **extract_item(descr2))
                                descr2.extract()
                            descriptions_dict = dict(descriptions_dict, **extract_item(descr))
                    lang_dict[lang.lower()] = descriptions_dict
            translations.append((sense, lang_dict))
                
        
        return translations
        
        
    # fix verb/noun not working! problem in what this function returns!!
    def parse_translations(self, word_contents=None, return_tag_translations=False):
        word_contents = word_contents or self.word_contents
        translations_id_list = self.get_id_list(word_contents, 'translations')
        translations_list = []
        translations_tags = []

        for translations_index, translations_id, _ in translations_id_list:
            cur_transl_dict = self.parse_translations_attempt(language=self.language, soup=self.soup, translations_id=translations_id)
            
            if len(cur_transl_dict) == 1 and '/translations' in cur_transl_dict[0].text:
                url = cur_transl_dict[0].find('a').get('href').replace('/wiki/','')

                session2 = requests.Session()
                session2.mount("http://", requests.adapters.HTTPAdapter(max_retries = 2))
                session2.mount("https://", requests.adapters.HTTPAdapter(max_retries = 2))
                response = session2.get(self.url.format(self.url_preffix, url))
                soup2 = BeautifulSoup(response.text.replace('>\n','><'), 'html.parser')
                span = soup2.find('span',{'id':url.split('#')[1]}).parent.find_next_sibling()
                self._span = span
                self._soup2 = soup2
                
                translations_id_list2 = self.get_id_list(content_type='translations', soup=soup2)
                
                
                cur_transl_dict = []
                #print('tr_id_l2', translations_id_list2)
                #print('soup2', soup2)
                for translations_index2, translations_id2, _2 in translations_id_list2:
                    cur_transl_dict = self.parse_translations_attempt(language=self.language, span=span, translations_id=translations_id2)
                    #cur_transl_dict.extend(cur_transl_dict2)
                
            
            translations_dicts = self.extract_languages(cur_transl_dict)
            
            translations_list.append((translations_index, translations_dicts))
                
        if return_tag_translations: return translations_tags
        return translations_list
    

    def parse_translations0(self, word_contents=None, return_tag_translations=False):
        word_contents = word_contents or self.word_contents
        translations_id_list = self.get_id_list(word_contents, 'translations')
        translations_list = []
        translations_tags = []
        for translations_index, translations_id, _ in translations_id_list:
            span_tag = self.soup.find_all('span', {'id': translations_id})[0]
            if span_tag == []:
                pass
            transl_siblings = []
            transl_tag = None
            next_tag = span_tag.parent.find_next_sibling()
            while next_tag.name not in ['h3','h4','h5',]:
                transl_tag = next_tag
                next_tag = next_tag.find_next_sibling()
                transl_siblings.append(transl_tag)
            
            
            if len(transl_siblings) == 1 and '/translations' in transl_siblings[0].text:
                url = transl_siblings[0].find('a').get('href')
                response = self.session.get(self.url.format(self.url_preffix, url))
                soup2 = BeautifulSoup(response.text.replace('>\n','><'), 'html.parser')
                
                raise NotImplementedError('Translations in separated link')
            else:
                translations_dicts = self.extract_languages(transl_siblings)
            
            
            translations_list.append((translations_index, translations_dicts))
        
        if return_tag_translations: return translations_tags
        return translations_list
    
    def parse_translations_attempt(self, language, span=None, soup=None, translations_id=None, word_contents=None, return_tag_translations=False):
        if soup:
            word_contents = word_contents or self.get_word_contents(language, soup)
            span_tag = soup.find_all('span', {'id': translations_id})[0]
            transl_tag = span_tag.parent.find_next_sibling()
        else:
            print('here')
            transl_tag = span.find_next_sibling()
            print(span.find_next_sibling())
        self._transl_tag.append(transl_tag)
        transl_siblings = []
        while True:
            try:
                transl_tag_name = transl_tag.name
            except:
                transl_tag_name = None
            if transl_tag_name in ['h3','h4','h5',None]:
                break

            transl_siblings.append(transl_tag)
            transl_tag = transl_tag.find_next_sibling()
        
        return transl_siblings
        
        #if return_tag_translations: return translations_tags
        #return translations_list

    def map_to_object(self, word_data):
        json_obj_list = []
        if not word_data['etymologies']:
            word_data['etymologies'] = [('', '')]
        for (current_etymology, next_etymology) in zip_longest(word_data['etymologies'], word_data['etymologies'][1:], fillvalue=('999', '')):
            data_obj = WordData()
            data_obj.etymology = current_etymology[1]
            for pronunciation_index, text, audio_links in word_data['pronunciations']:
                if (self.count_digits(current_etymology[0]) == self.count_digits(pronunciation_index)) or (current_etymology[0] <= pronunciation_index < next_etymology[0]):
                    data_obj.pronunciations = text
                    data_obj.audio_links = audio_links
            for definition_index, definition_text, definition_type in word_data['definitions']:
                if current_etymology[0] <= definition_index < next_etymology[0]:
                    print('\n>>', definition_index, definition_text)
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
                        #print(translations_index, definition_index)
                        #print('here', translations_dict)
                        if translations_index.startswith(".".join(definition_index.split(".", 3)[:3])):
                            def_obj.translations = translations_dict
                            found = True
                    if not found:
                        for translations_index, translations_dict in word_data['translations']:
                            print(translations_index, definition_index)
                            #print('here', translations_dict)
                            if translations_index.startswith(".".join(definition_index.split(".", 2)[:2])):
                                def_obj.translations = translations_dict
                                found = True                   
                    data_obj.definition_list.append(def_obj)
#            for translations_index, translations_dict in word_data['translations']:
#                if (self.count_digits(current_etymology[0]) == self.count_digits(translations_index)) or (current_etymology[0] <= translations_index < next_etymology[0]):
#                    data_obj.translations = translations_dict
            #return(data_obj)
            json_obj_list.append(data_obj.to_json())
        return json_obj_list


    def map_to_object0(self, word_data):
        json_obj_list = []
        if not word_data['etymologies']:
            word_data['etymologies'] = [('', '')]
        for (current_etymology, next_etymology) in zip_longest(word_data['etymologies'], word_data['etymologies'][1:], fillvalue=('999', '')):
            data_obj = WordData()
            data_obj.etymology = current_etymology[1]
            for pronunciation_index, text, audio_links in word_data['pronunciations']:
                if (self.count_digits(current_etymology[0]) == self.count_digits(pronunciation_index)) or (current_etymology[0] <= pronunciation_index < next_etymology[0]):
                    data_obj.pronunciations = text
                    data_obj.audio_links = audio_links
            for definition_index, definition_text, definition_type in word_data['definitions']:
                if current_etymology[0] <= definition_index < next_etymology[0]:
                    def_obj = Definition()
                    def_obj.text = definition_text
                    def_obj.part_of_speech = definition_type
                    for example_index, examples, _ in word_data['examples']:
                        if example_index.startswith(definition_index):
                            def_obj.example_uses = examples
                    for related_word_index, related_words, relation_type in word_data['related']:
                        if related_word_index.startswith(definition_index):
                            def_obj.related_words.append(RelatedWord(relation_type, related_words))
                    data_obj.definition_list.append(def_obj)
            for translations_index, translations_dict in word_data['translations']:
                if (self.count_digits(current_etymology[0]) == self.count_digits(translations_index)) or (current_etymology[0] <= translations_index < next_etymology[0]):
                    data_obj.translations = translations_dict
            json_obj_list.append(data_obj.to_json())
        return json_obj_list

    def fetch(self, word, language=None):
        language = language or self.language
        response = self.session.get(self.url.format(self.url_preffix, word))
        self.soup = BeautifulSoup(response.text.replace('>\n<', '><'), 'html.parser')
        self.current_word = word
        self.clean_html()
        return self.get_word_data(language.lower())