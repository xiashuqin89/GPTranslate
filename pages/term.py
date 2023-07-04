import os
import json
from typing import List

import streamlit as st
import pandas as pd
from PIL import Image

from settings import DOMAIN
from elements.magic import Login, post_compile
from exceptions import LoginFailedError
from log import logger
from utils.stdlib import Tool

APP_CODE = os.getenv('BKPAAS_APP_ID')
APP_ENV = os.getenv('BKPAAS_ENVIRONMENT')


class Term(Login, Tool):
    def __init__(self):
        super(Term, self).__init__()
        Tool.__init__(self)
        self.project = ''

    def sidebar(self):
        st.sidebar.title('Template')
        image = Image.open('media/term_template.png')
        st.sidebar.image(image, caption='edit excel like this')
        project = tuple(self.get_project(self.username, 'project_name'))
        self.project = st.sidebar.selectbox('Project', project)

    def toolbar(self):
        with st.expander("Add"):
            if self.project == '':
                st.warning(f'your need select a project')
            else:
                uploaded_file = st.file_uploader("Choose a excel file", type=['xlsx'],
                                                 help='only support xlsx')
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
        # need to change to true kv mode
        term = {item[0]: item[1] for item in term}
        self.rc.hash_set(f'{APP_CODE}:{APP_ENV}:term:{self.project}',
                         name, json.dumps(term))

    def render(self):
        st.subheader('Term')
        self.sidebar()
        self.toolbar()
        self.data()


@post_compile('ko2cn', DOMAIN)
def main():
    try:
        Term().render()
    except LoginFailedError:
        logger.error('login failed')


if __name__ == '__main__':
    main()
