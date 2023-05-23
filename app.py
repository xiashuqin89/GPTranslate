import streamlit as st
from langdetect import detect

from settings import DOMAIN
from elements.magic import (
    get_headers, post_compile, get_cookie_val
)


class Engine:
    def __init__(self):
        self.username = get_cookie_val("t_uid")
        self.input_type = 'Text'
        self.project = ''
        self.language = ''

    def debug(self):
        st.code(get_headers(), language='python')

    def menu(self):
        st.sidebar.text(self.username)
        st.sidebar.title('Menu')
        self.project = st.sidebar.selectbox('Poject', ('project1', 'project2'))
        self.input_type = st.sidebar.selectbox("Input Type", ('Text', 'File'))

    def text_translate(self):
        option_col1, option_col2, _ = st.columns([2, 2, 8])
        with option_col1:
            language = st.selectbox('', ('korea',))
        with option_col2:
            term = st.multiselect('', ['term1', 'term2'])

        input_col1, input_col2 = st.columns(2)
        with input_col1:
            user_input = st.text_area('Your input', height=30)
            if user_input != '':
                language = detect(user_input)
                st.write(f'Lang:  {language}')

        with input_col2:
            status = 'waiting for input'
            if user_input != '':
                status = 'translating...'
            output = st.text_area('Chinese', placeholder=status)

    def file_translate(self):
        uploaded_file = st.file_uploader("Choose a file")
        if uploaded_file is not None:
            # To read file as bytes:
            bytes_data = uploaded_file.getvalue()
            st.write(bytes_data)

    def render(self):
        self.menu()
        st.title('Debug')
        if self.input_type == 'Text':
            self.text_translate()
        elif self.input_type == 'File':
            self.file_translate()


@post_compile('ko2cn', DOMAIN)
def main():
    Engine().render()


if __name__ == '__main__':
    main()
