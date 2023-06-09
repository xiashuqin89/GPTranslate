import os
import json
import time
from typing import Tuple, Dict, SupportsBytes

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from streamlit.delta_generator import DeltaGenerator
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder
import diff_viewer
import pandas as pd
import numpy as np
from docx import Document
from langdetect import detect

from settings import DOMAIN, LANGUAGE, MODEL, BK_REPO_ROOT
from elements.magic import (
    post_compile, Login
)
from api.dolph import translate
from api.bkrepo import BKRepo
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

    def get_record_list(self) -> Dict:
        return self.rc.redis_client.hgetall(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.username}')

    def get_record(self, key: str) -> Dict:
        data = self.rc.hash_get(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.username}', key)
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}

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
        params.update({'pure_text': pure_text})
        self.rc.hash_set(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.username}',
                         time.strftime('%Y-%m-%d %H:%M:%S'), json.dumps(params))
        return

    def file_diff(self, record: Dict, msg: DeltaGenerator):
        raw = self.get_record(record['time'])
        data = BKRepo().search({
            "rules": [
                {"field": "projectId", "value": "opsbot2", "operation": "EQ"},
                {"field": "repoName", "value": "translate", "operation": "EQ"},
                {"field": "path", "value": "/target/", "operation": "EQ"},
                {"field": "name", "value": raw['file_name'], "operation": "EQ"}
            ],
            "relation": "AND"
        })

        if data['count'] == 0:
            msg.info('Translate task still running...')
        else:
            msg.success('Translated')
            self.file_download(record['filename'])
            diff_viewer.diff_viewer(old_text=raw['pure_text'],
                                    new_text='Translating...',
                                    lang='python')

    def file_parse(self, uploaded_file: UploadedFile, msg: DeltaGenerator) -> Tuple:
        if uploaded_file is not None:
            msg.info('Parsing...')
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
            return filename, extract_type, pure_text, bytes_data
        return None

    def file_download(self, filename: str):
        st.markdown(f"""
            <a href="{BK_REPO_ROOT}/generic/opsbot2/translate/target/{filename}" target = "_blank"> 
                    
            </a>
        """, unsafe_allow_html=True)

    def file_list(self):
        data = self.get_record_list() or {}
        if data:
            # st.write('Record')
            st.divider()
            st.subheader('Record')
        else:
            return
        data = pd.DataFrame([{'time': k, 'filename': json.loads(v)['file_name']} for k, v in data.items()])
        gb = GridOptionsBuilder.from_dataframe(data)
        gb.configure_selection(selection_mode='single')
        gb.configure_auto_height()
        gb.configure_side_bar()
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
        go = gb.build()
        return_ag = AgGrid(data,
                           enable_quicksearch=True,
                           gridOptions=go,
                           allow_unsafe_jscode=True,
                           reload_data=False,
                           use_legacy_selected_rows=True,
                           fit_columns_on_grid_load=True,
                           update_mode=GridUpdateMode.SELECTION_CHANGED)
        return return_ag.selected_rows

    def render(self):
        st.title('Bkchatranslate')
        self.menu()
        if self.input_type == 'Text':
            self.text_translate()
        elif self.input_type == 'File':
            uploaded_file = st.file_uploader("Choose a file")
            msg = st.empty()
            if st.button('Submit', use_container_width=True):
                file_info = self.file_parse(uploaded_file, msg)
                if file_info is not None:
                    self.file_translate(*file_info)
                    msg.success('Task Add')
                else:
                    msg.warning('Error: plz check your upload file')
            selected_rows = self.file_list()
            if selected_rows:
                self.file_diff(selected_rows[0], msg)


@post_compile('ko2cn', DOMAIN)
def main():
    try:
        Engine().render()
    except LoginFailedError:
        logger.error('login failed')


if __name__ == '__main__':
    main()
