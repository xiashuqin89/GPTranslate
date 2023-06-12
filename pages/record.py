import os
import io
import json
from typing import Dict

import pandas as pd
import numpy as np
import streamlit as st
import diff_viewer
from docx import Document
from streamlit.delta_generator import DeltaGenerator
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder

from elements.magic import Login
from utils.db import RedisClient
from exceptions import LoginFailedError
from api.bkrepo import BKRepo
from log import logger

APP_CODE = os.getenv('BKPAAS_APP_ID')
APP_ENV = os.getenv('BKPAAS_ENVIRONMENT')


class Record(Login):
    def __init__(self):
        super(Record, self).__init__()
        self.project = ''
        self.rc = RedisClient(env="prod")

    def get_project(self):
        project = self.rc.redis_client.hvals(f'{APP_CODE}:{APP_ENV}:project:{self.username}')
        if not project:
            return []
        return [json.loads(item)['project_name'] for item in project]

    def get_record_list(self) -> Dict:
        return self.rc.redis_client.hgetall(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.username}')

    def get_record(self, key: str) -> Dict:
        data = self.rc.hash_get(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.username}', key)
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}

    def siderbar(self):
        st.sidebar.title('Project')
        project = self.get_project()
        self.project = st.sidebar.selectbox('Project', tuple(project))

    def file_list(self):
        with st.spinner('Wait for loading...'):
            data = self.get_record_list() or {}
            if data:
                st.subheader('Record')
            else:
                st.subheader('Record')
                st.warning('No Record')
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

    def file_diff(self, record: Dict, msg: DeltaGenerator):
        raw = self.get_record(record['time'])
        bk_repo = BKRepo()
        data = bk_repo.search({
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
            response = bk_repo.download('opsbot2', 'translate', f"target/{raw['file_name']}", stream=True)
            bytes_data = response.content
            new_text = ''
            if raw['extract_type'] == 'xlsx':
                new_text = self.excel2text(bytes_data)
            elif raw['extract_type'] == 'docx':
                source_stream = Document(io.BytesIO(bytes_data))
                new_text = '\n'.join([para.text for para in source_stream.paragraphs])

            self.file_download(record['filename'], raw['extract_type'], bytes_data)
            diff_viewer.diff_viewer(old_text=raw['pure_text'],
                                    new_text=new_text,
                                    lang='python')

    def file_download(self, filename: str, extract_type: str, data: bytes):
        st.download_button(
            label="Press to download",
            data=data,
            file_name=filename,
            mime=f'text/{extract_type}',
        )

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
        self.siderbar()
        msg = st.empty()
        selected_rows = self.file_list()
        if selected_rows:
            self.file_diff(selected_rows[0], msg)


def main():
    try:
        Record().render()
    except LoginFailedError:
        logger.error('login failed')


if __name__ == '__main__':
    main()
