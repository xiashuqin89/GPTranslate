import streamlit as st
from PIL import Image

class Term:
    def __init__(self):
        pass

    def siderbar(self):
        st.sidebar.title('Template')
        image = Image.open('media/term_template.png')
        st.sidebar.image(image, caption='Sunrise by the mountains')

    def toolbar(self):
        uploaded_file = st.file_uploader("Choose a excel file",
                                         type=['csv', 'xlsx', 'xls'],
                                         help='only support csv, xlsx, xls')
        if uploaded_file is not None:
            print(uploaded_file)

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
        self.siderbar()
        self.toolbar()
        self.data()


Term().render()
