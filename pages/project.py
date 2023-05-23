import streamlit as st

from settings import WHITE_MEMBERS
from elements.magic import Login
from exceptions import LoginFailedError
from log import logger


class Project(Login):
    def __init__(self):
        super(Project, self).__init__()
        self.is_new = None

    def toolbar(self):
        tool_col1, tool_col2, _ = st.columns([2, 2, 8])
        with tool_col1:
            self.is_new = st.button('New')
            if self.is_new:
                if not st.session_state.get('is_new'):
                    st.session_state['is_new'] = True
                else:
                    st.session_state['is_new'] = False

    def dialog(self):
        with st.form("new_project"):
            st.write("New Project")
            project_name = st.text_input('Project Name')
            members = st.multiselect('', WHITE_MEMBERS)

            st.session_state['project_name'] = project_name
            st.session_state['members'] = members
            # Every form must have a submit button.
            submitted = st.form_submit_button("Submit")
            if submitted:
                pass

    def data(self):
        hide_table_row_index = """
            <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
            </style>
        """
        st.markdown(hide_table_row_index, unsafe_allow_html=True)
        st.table([{'a': 1, 'b': 2}, {'a': 3, 'b': 4}])

    def render(self):
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
