import os
import io
import json
import time
from typing import Tuple

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from streamlit.delta_generator import DeltaGenerator
import pandas as pd
import numpy as np
from docx import Document
from langdetect import detect

from settings import DOMAIN, LANGUAGE, MODEL
from elements.magic import (
    post_compile, Login, nav_page
)
from api.dolph import translate
from exceptions import LoginFailedError
from utils.db import RedisClient
from log import logger

APP_CODE = os.getenv('BKPAAS_APP_ID')
APP_ENV = os.getenv('BKPAAS_ENVIRONMENT')


class Engine(Login):
    def __init__(self):
        super(Engine, self).__init__()
        self.input_type = 'Text'
        self.project = ''
        self.language = ''
        self.model = ''
        self.term = ''
        self.rc = RedisClient(env="prod")

    def get_project(self):
        projects = self.rc.redis_client.hvals(f'{APP_CODE}:{APP_ENV}:project')
        if not projects:
            return []
        try:
            for item in projects:
                item = json.loads(item)
                if self.username in item['members']:
                    yield item['project_name']
        except json.JSONDecodeError:
            return []

    def get_term(self):
        return self.rc.redis_client.hkeys(f'{APP_CODE}:{APP_ENV}:term:{self.project}')

    def menu(self):
        st.sidebar.text(self.username)
        st.sidebar.title('Menu')
        project = self.get_project()
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
        logger.debug(response)
        params.update({'pure_text': pure_text, 'task_id': response.get('task_id', '')})
        self.rc.hash_set(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.username}',
                         time.strftime('%Y-%m-%d %H:%M:%S'), json.dumps(params))
        return

    def file_parse(self, uploaded_file: UploadedFile, msg: DeltaGenerator) -> Tuple:
        if uploaded_file is not None:
            msg.info('Parsing...')
            pure_text, bytes_data = '', uploaded_file.getvalue()
            filename = uploaded_file.name
            extract_type = ''
            print(uploaded_file.name)
            if uploaded_file.name.endswith('xlsx'):
                extract_type = 'xlsx'
                pure_text = self.excel2text(uploaded_file)
            elif uploaded_file.name.endswith('docx'):
                extract_type = 'docx'
                source_stream = Document(io.BytesIO(bytes_data))
                pure_text = '\n'.join([para.text for para in source_stream.paragraphs])
            return filename, extract_type, pure_text, bytes_data
        return None

    def excel2text(self, data: bytes):
        pure_text = ''
        sheets = pd.read_excel(data, sheet_name=None)
        for k, v in sheets.items():
            pure_text += k
            for row in v.values.tolist():
                for col in row:
                    if col is np.nan or str(col) == 'nan':
                        pure_text += ' '
                    else:
                        pure_text += str(col)
                pure_text += '\n'
        return pure_text

    def render(self):
        st.title('Bkchatranslate')
        self.menu()
        if self.input_type == 'Text':
            self.text_translate()
        elif self.input_type == 'File':
            uploaded_file = st.file_uploader("Choose a file", type=['xlsx', 'docx'])
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
