import os
import json

import streamlit as st

from settings import WHITE_MEMBERS, DOMAIN
from elements.magic import Login, post_compile
from exceptions import LoginFailedError
from log import logger
from utils.stdlib import Tool


APP_CODE = os.getenv('BKPAAS_APP_ID')
APP_ENV = os.getenv('BKPAAS_ENVIRONMENT')


class Project(Login, Tool):
    def __init__(self):
        super(Project, self).__init__()
        Tool.__init__(self)
        self.is_new = None

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
                if self.rc.redis_client.hexists(f'{APP_CODE}:{APP_ENV}:project', project_name):
                    msg.error('Project name exist...')
                    return
                members.append(self.username)
                self.rc.hash_set(f'{APP_CODE}:{APP_ENV}:project',
                                 project_name,
                                 json.dumps({'project_name': project_name, 'members': list(set(members)),
                                             'creator': self.username}))
                msg.success('Created')

    def data(self):
        hide_table_row_index = """
            <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
            </style>
        """
        st.markdown(hide_table_row_index, unsafe_allow_html=True)
        projects = self.get_project(self.username)
        st.table(list(projects))

    def render(self):
        st.subheader('Project')
        self.toolbar()
        if st.session_state.get('is_new'):
            self.dialog()
        self.data()


@post_compile('ko2cn', DOMAIN)
def main():
    try:
        Project().render()
    except LoginFailedError:
        logger.error('login failed')


if __name__ == '__main__':
    main()
