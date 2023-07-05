import os
import io
import json
from typing import Dict

import pandas as pd
import streamlit as st
import diff_viewer
from docx import Document
from streamlit.delta_generator import DeltaGenerator
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder

from elements.magic import Login, post_compile
from exceptions import LoginFailedError
from api.bkrepo import BKRepo
from api.dolph import translate as check_translate_status
from log import logger
from utils.stdlib import Tool
from settings import SUPERUSER, WHITE_MEMBERS, DOMAIN

APP_CODE = os.getenv('BKPAAS_APP_ID')
APP_ENV = os.getenv('BKPAAS_ENVIRONMENT')


class Record(Login, Tool):
    def __init__(self):
        super(Record, self).__init__()
        Tool.__init__(self)
        self.project = ''
        self.query = self.username

    def get_record_list(self) -> Dict:
        return self.rc.redis_client.hgetall(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.query}')

    def get_record(self, key: str) -> Dict:
        data = self.rc.hash_get(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.query}', key)
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}

    def sidebar(self):
        st.sidebar.title('Project')
        project = self.get_project(self.username, 'project_name')
        self.project = st.sidebar.selectbox('Project', tuple(project))
        if self.username in SUPERUSER:
            admin = st.sidebar.selectbox('Members', WHITE_MEMBERS)
            if st.sidebar.button('GM', use_container_width=True):
                self.query = admin

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

    def _status_handle(self, raw: Dict, msg: DeltaGenerator):
        try:
            task_id = raw['response']['task_id']
        except KeyError:
            msg.error('No task id found... or this is a old task...')
            return
        response = check_translate_status({'bk_ticket': self.bk_ticket}, 'check_status', task_id=task_id)
        data = response.get('data', {'status': 'PENDING'})
        if data['status'] == 'PROGRESS':
            result = data["result"]
            progress_text = f'Translate task still running... Total character: ' \
                            f'{result["total"]}, complete: {result["current"]}'
            st.progress(result["percent"], text=progress_text)
        elif data['status'] == 'FAILURE':
            msg.error('Translate task absolutely failed...')
        elif data['status'] == 'PENDING':
            msg.error('Translate task is pending now, maybe task queue is blocked...')

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
            self._status_handle(raw, msg)
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

    def render(self):
        self.sidebar()
        msg = st.empty()
        selected_rows = self.file_list()
        if selected_rows:
            self.file_diff(selected_rows[0], msg)


@post_compile('ko2cn', DOMAIN)
def main():
    try:
        Record().render()
    except LoginFailedError:
        logger.error('login failed')


if __name__ == '__main__':
    main()
