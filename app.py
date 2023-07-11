import os
import json
import time
from typing import Tuple

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from streamlit.delta_generator import DeltaGenerator
from langdetect import detect

from settings import DOMAIN, LANGUAGE, MODEL
from elements.magic import (
    post_compile, Login, nav_page
)
from api.dolph import translate
from exceptions import LoginFailedError
from utils.stdlib import Tool
from utils.parser import FileParser
from log import logger

APP_CODE = os.getenv('BKPAAS_APP_ID')
APP_ENV = os.getenv('BKPAAS_ENVIRONMENT')


class Engine(Login, Tool):
    def __init__(self):
        super(Engine, self).__init__()
        Tool.__init__(self)
        self.input_type = 'Text'
        self.project = ''
        self.language = ''
        self.model = ''
        self.term = ''

    def get_term(self):
        return self.rc.redis_client.hkeys(f'{APP_CODE}:{APP_ENV}:term:{self.project}')

    def menu(self):
        st.sidebar.text(self.username)
        st.sidebar.title('Menu')
        project = self.get_project(self.username, 'project_name')
        self.project = st.sidebar.selectbox('Project', tuple(project))
        self.input_type = st.sidebar.selectbox("Input Type", ('Text', 'File'))

        option_col1, option_col2, option_col3, _ = st.columns([2, 2, 4, 4])
        with option_col1:
            self.model = st.selectbox('model', tuple(MODEL))
        with option_col2:
            self.language = st.selectbox('lang', tuple(LANGUAGE))
        with option_col3:
            self.term = st.multiselect('term', self.get_term(), label_visibility='hidden')

    def text_translate(self):
        msg = st.empty()
        input_col1, input_col2 = st.columns(2)
        with input_col1:
            user_input = st.text_area('Your input', height=30)
            if user_input != '':
                language = detect(user_input)
                st.write(f'Lang:  {language}')

        with input_col2:
            status = 'waiting for input'
            output = ''
            if user_input != '':
                status = 'translating...'
                response = translate({'bk_ticket': self.bk_ticket},
                                     text=user_input,
                                     translate_type=self.model,
                                     term=self.term,
                                     project=self.project)
                output = response.get('data', {}).get('result')
                if output is None:
                    output = 'no response'
                    msg.error('the backend api error...')
            st.text_area('Chinese', output, placeholder=status)

    def file_translate(self, filename: str, extract_type: str, pure_text: str, bytes_data: bytes):
        params = {
            "term": self.term,
            "project": self.project,
            "extract_type": extract_type,
            "file_name": filename,
            "file": bytes_data.decode('latin-1'),
            "translate_type": self.model
        }
        response = translate({'bk_ticket': self.bk_ticket}, 'translate_file', **params)
        logger.error(response)
        params.update({'pure_text': pure_text, 'response': response.get('data', {})})
        self.rc.hash_set(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.username}',
                         time.strftime('%Y-%m-%d %H:%M:%S'), json.dumps(params))
        return

    def file_parse(self, uploaded_file: UploadedFile, msg: DeltaGenerator) -> Tuple:
        if uploaded_file is not None:
            msg.info('Parsing...')
            pure_text, bytes_data = '', uploaded_file.getvalue()
            filename = uploaded_file.name
            parser = FileParser(uploaded_file.name)
            extract_type = parser.filetype
            # temp transfer txt/pdf to docx
            if extract_type in ['txt', 'pdf']:
                extract_type = 'docx'
            pure_text = parser.tostring(bytes_data)
            return filename, extract_type, pure_text, bytes_data
        return None

    def render(self):
        st.title('Bkchatranslate')
        self.menu()
        if self.input_type == 'Text':
            self.text_translate()
        elif self.input_type == 'File':
            uploaded_file = st.file_uploader("Choose a file", type=['xlsx', 'docx', 'pdf', 'txt'])
            msg = st.empty()
            if st.button('Submit', use_container_width=True):
                file_info = self.file_parse(uploaded_file, msg)
                if file_info is not None:
                    self.file_translate(*file_info)
                    msg.success('Task Add')
                    nav_page('record')
                else:
                    msg.error('Error: plz check your upload file')


@post_compile('ko2cn', DOMAIN)
def main():
    try:
        Engine().render()
    except LoginFailedError:
        logger.error('login failed')


if __name__ == '__main__':
    main()
