import os
import json
import time
from typing import Tuple, Dict

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from streamlit.delta_generator import DeltaGenerator
import diff_viewer
import pandas as pd
import numpy as np
from docx import Document
from langdetect import detect

from settings import DOMAIN, LANGUAGE, MODEL
from elements.magic import (
    post_compile, Login
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
        project = self.rc.redis_client.hvals(f'{APP_CODE}:{APP_ENV}:project:{self.username}')
        if not project:
            return []
        return [json.loads(item)['project_name'] for item in project]

    def get_term(self):
        return self.rc.redis_client.hkeys(f'{APP_CODE}:{APP_ENV}:term:{self.project}')

    def get_record(self) -> Dict:
        return self.rc.redis_client.hgetall(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.username}')

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
            st.text_area('Chinese', output, placeholder=status)

    def file_translate(self):
        uploaded_file = st.file_uploader("Choose a file")
        msg = st.empty()
        result = self.file_parse(uploaded_file, msg)
        if result:
            msg.success('Translated')
            self.file_download()
            diff_viewer.diff_viewer(old_text=result[0],
                                    new_text='Translating...',
                                    lang='python')

    def file_parse(self, uploaded_file: UploadedFile, msg: DeltaGenerator) -> Tuple:
        if uploaded_file is not None:
            msg.info('Translating...')
            pure_text, bytes_data = '', uploaded_file.getvalue()
            filename = uploaded_file.name
            extract_type = ''
            if uploaded_file.name.endswith('xlsx'):
                extract_type = 'xlsx'
                df = pd.read_excel(uploaded_file)
                for row in df.values.tolist():
                    for col in row:
                        if col is np.nan or str(col) == 'nan':
                            pure_text += ' '
                        else:
                            pure_text += str(col)
                    pure_text += '\n'
            elif uploaded_file.name.endswith('docx'):
                extract_type = 'docx'
                import io
                source_stream = Document(io.BytesIO(bytes_data))
                pure_text = '\n'.join([para.text for para in source_stream.paragraphs])

            if extract_type:
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
                self.rc.hash_set(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.username}',
                                 time.strftime('%Y-%m-%d %H:%M:%S'), json.dumps(params))

            return pure_text, bytes_data
        return None

    def file_download(self, df: pd.DataFrame = None):
        if df:
            df.to_excel('media/large_df.xlsx')
            with open("media/large_df.xlsx", "rb") as file:
                st.download_button(
                    label="Download data as Excel",
                    data=file,
                    file_name='large_df.xlsx',
                    mime='text/xlsx',
                )

    def file_list(self):
        data = self.get_record() or {}
        data = [{'time': k, 'filename': v} for k, v in data.items()]
        st.table(data)

    def render(self):
        st.title('Bkchatanslate')
        self.menu()
        if self.input_type == 'Text':
            self.text_translate()
        elif self.input_type == 'File':
            self.file_translate()
            self.file_list()


@post_compile('ko2cn', DOMAIN)
def main():
    try:
        Engine().render()
    except LoginFailedError:
        logger.error('login failed')


if __name__ == '__main__':
    main()
