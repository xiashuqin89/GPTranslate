import streamlit as st

from settings import DOMAIN
from elements.magic import (
    get_headers, post_compile, get_cookie_val
)


@post_compile('ko2cn', DOMAIN)
def main():
    st.sidebar.title('Navigation')
    st.sidebar.text('This is some text.')
    st.title('This is a title')
    st.header(f'Hi, {get_cookie_val("t_uid")}')
    st.code(get_headers(), language='python')


if __name__ == '__main__':
    main()
