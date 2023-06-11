import os
import json
from typing import List

import streamlit as st
import pandas as pd
from PIL import Image

from elements.magic import Login
from exceptions import LoginFailedError
from log import logger
from utils.db import RedisClient

APP_CODE = os.getenv('BKPAAS_APP_ID')
APP_ENV = os.getenv('BKPAAS_ENVIRONMENT')


class Term(Login):
    def __init__(self):
        super(Term, self).__init__()
        self.project = ''
        self.rc = RedisClient(env="prod")

    def get_project(self):
        project = self.rc.redis_client.hvals(f'{APP_CODE}:{APP_ENV}:project:{self.username}')
        if not project:
            return []
        return [json.loads(item)['project_name'] for item in project]

    def sidebar(self):
        st.sidebar.title('Template')
        image = Image.open('media/term_template.png')
        st.sidebar.image(image, caption='edit excel like this')
        project = self.get_project()
        self.project = st.sidebar.selectbox('Project', tuple(project))

    def toolbar(self):
        with st.expander("Add"):
            if self.project == '':
                st.warning(f'your need select a project')
            else:
                uploaded_file = st.file_uploader("Choose a excel file",
                                                 type=['csv', 'xlsx', 'xls'],
                                                 help='only support csv, xlsx, xls')
                if uploaded_file is not None:
                    msg = st.empty()
                    msg.info('Upload...')
                    name = uploaded_file.name
                    df = pd.read_excel(uploaded_file)
                    st.table(df)
                    if self.rc.redis_client.hexists(f'{APP_CODE}:{APP_ENV}:term:{self.project}', name):
                        msg.warning(f'{name} will be override')
                    else:
                        msg.success('Uploaded')
                    self.save(name, df.values.tolist())

    def data(self):
        hide_table_row_index = """
            <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
            </style>
        """
        st.markdown(hide_table_row_index, unsafe_allow_html=True)
        data = self.rc.redis_client.hgetall(f'{APP_CODE}:{APP_ENV}:term:{self.project}')
        st.table([{'name': name, 'user': self.username} for name in data.keys()])

    def save(self, name: str, term: List[List[str]]):
        term = {item[0]: item[1] for item in term}
        self.rc.hash_set(f'{APP_CODE}:{APP_ENV}:term:{self.project}',
                         name, json.dumps(term))

    def render(self):
        st.subheader('Term')
        self.sidebar()
        self.toolbar()
        self.data()


def main():
    try:
        Term().render()
    except LoginFailedError:
        logger.error('login failed')


if __name__ == '__main__':
    main()
