import os
import json
import uuid

import streamlit as st

from settings import WHITE_MEMBERS
from elements.magic import Login
from exceptions import LoginFailedError
from log import logger
from utils.db import RedisClient


APP_CODE = os.getenv('BKPAAS_APP_ID')
APP_ENV = os.getenv('BKPAAS_ENVIRONMENT')


class Project(Login):
    def __init__(self):
        super(Project, self).__init__()
        self.is_new = None
        self.rc = RedisClient(env="prod")

    def toolbar(self):
        tool_col1, tool_col2, _ = st.columns([2, 2, 8])
        with tool_col1:
            self.is_new = st.button('Add')
            if self.is_new:
                if not st.session_state.get('is_new'):
                    st.session_state['is_new'] = True
                else:
                    st.session_state['is_new'] = False

    def dialog(self):
        with st.form("new_project"):
            st.write("New Project")
            project_name = st.text_input('Project Name')
            members = st.multiselect('Members', WHITE_MEMBERS)

            st.session_state['project_name'] = project_name
            st.session_state['members'] = members
            # Every form must have a submit button.
            submitted = st.form_submit_button("Submit")
            if submitted:
                msg = st.empty()
                msg.info('Creating...')
                self.rc.hash_set(f'{APP_CODE}:{APP_ENV}:project:{self.username}',
                                 str(uuid.uuid4()),
                                 json.dumps({'project_name': project_name, 'members': members}))
                msg.success('Created')

    def data(self):
        hide_table_row_index = """
            <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
            </style>
        """
        st.markdown(hide_table_row_index, unsafe_allow_html=True)
        project = self.rc.redis_client.hvals(f'{APP_CODE}:{APP_ENV}:project:{self.username}')
        st.table([json.loads(item) for item in project])

    def render(self):
        st.subheader('Project')
        self.toolbar()
        if st.session_state.get('is_new'):
            self.dialog()
        self.data()


def main():
    try:
        Project().render()
    except LoginFailedError:
        logger.error('login failed')


if __name__ == '__main__':
    main()
