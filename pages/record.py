import os
import json
from typing import Dict, List, Generator

import pandas as pd
import streamlit as st
import diff_viewer
from streamlit.delta_generator import DeltaGenerator
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder

from elements.magic import Login, post_compile
from exceptions import LoginFailedError
from api.bkrepo import BKRepo
from api.dolph import translate as check_translate_status
from log import logger
from utils.stdlib import Tool
from utils.parser import FileParser
from settings import SUPERUSER, WHITE_MEMBERS, DOMAIN

APP_CODE = os.getenv('BKPAAS_APP_ID')
APP_ENV = os.getenv('BKPAAS_ENVIRONMENT')


class Record(Login, Tool):
    def __init__(self):
        super(Record, self).__init__()
        Tool.__init__(self)
        self.project = ''
        self.query = self.username

    def get_record_list(self) -> Generator:
        data = self.rc.redis_client.hgetall(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.query}')
        for k, v in data.items():
            try:
                detail = json.loads(v)
            except json.JSONDecodeError:
                continue
            yield {'time': k, 'filename': detail['file_name'], 'status': detail.get('status', 'PENDING')}

    def get_record(self, key: str) -> Dict:
        data = self.rc.hash_get(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.query}', key)
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}

    def set_record(self, key, data):
        self.rc.hash_set(f'{APP_CODE}:{APP_ENV}:record:{self.project}:{self.query}', key, json.dumps(data))

    def sidebar(self):
        st.sidebar.title('Project')
        project = self.get_project(self.username, 'project_name')
        self.project = st.sidebar.selectbox('Project', tuple(project))
        if self.username in SUPERUSER:
            admin = st.sidebar.selectbox('Members', WHITE_MEMBERS)
            if st.sidebar.button('GM', use_container_width=True):
                self.query = admin

    def toolbar(self, toolbar: DeltaGenerator, msg: DeltaGenerator, selected_rows: List):
        col1, col2, col3, col4, _ = toolbar.columns([1, 1, 1, 1, 5])
        with col1:
            st.button('refresh', use_container_width=True)

        if not selected_rows:
            msg.info('please click a row')
            return

        with col2:
            if st.button('check', use_container_width=True):
                with st.spinner('parsing'):
                    self.file_diff(selected_rows[0], msg)
        with col3:
            st.button('retry', use_container_width=True)
        with col4:
            st.button('stop', use_container_width=True)

    def file_list(self):
        with st.spinner('Wait for loading...'):
            data = sorted(self.get_record_list(), key=lambda x: x['time'], reverse=True) or []
            if not data:
                st.warning('No Record')
                return
            data = pd.DataFrame(data)

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

    def _status_handle(self, raw: Dict, msg: DeltaGenerator) -> str:
        try:
            task_id = raw['response']['task_id']
        except KeyError:
            msg.error('No task id found... or this is a old task...')
            return 'UNKNOWN'
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
            msg.info('Translate task is pending now, maybe task queue is blocked...')
        return data['status']

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
            status = self._status_handle(raw, msg)
        else:
            msg.success('Translated')
            status = 'SUCCESS'
            response = bk_repo.download('opsbot2', 'translate', f"target/{raw['file_name']}", stream=True)
            bytes_data = response.content
            parser = FileParser()
            parser.filetype = raw['extract_type']
            new_text = parser.tostring(bytes_data)
            # mv download link to bkrepo
            self.file_download(record['filename'], raw['extract_type'], bytes_data)
            diff_viewer.diff_viewer(old_text=raw['pure_text'],
                                    new_text=new_text,
                                    lang='python')
        raw.update({'status': status})
        self.set_record(record['time'], raw)

    def file_download(self, filename: str, extract_type: str, data: bytes):
        st.download_button(
            label="Press to download",
            data=data,
            file_name=filename,
            mime=f'text/{extract_type}',
        )

    def render(self):
        st.subheader('Record')
        self.sidebar()
        msg = st.empty()
        toolbar = st.empty()
        selected_rows = self.file_list()
        self.toolbar(toolbar, msg, selected_rows)


@post_compile('ko2cn', DOMAIN)
def main():
    try:
        Record().render()
    except LoginFailedError:
        logger.error('login failed')


if __name__ == '__main__':
    main()
