import io

import pandas as pd
import numpy as np
from docx import Document


class FileParser:
    FILE_TYPE = (
        'xlsx',
        'docx',
        'txt',
        'sql',
        'pdf',
        'pptx'
    )

    def __init__(self, filename: str = ''):
        self.filename = filename
        self._filetype = ''
        if self.filename.endswith('xlsx'):
            self._filetype = 'xlsx'
        elif self.filename.endswith('docx'):
            self._filetype = 'docx'
        elif self.filename.endswith('pdf'):
            self._filetype = 'pdf'
        elif self.filename.endswith('pptx'):
            self._filetype = 'pptx'
        elif self.filename.endswith('txt'):
            self._filetype = 'txt'

    @property
    def filetype(self):
        return self._filetype

    @filetype.setter
    def filetype(self, value) -> None:
        self._filetype = value

    def tostring(self, data: bytes):
        return getattr(globals()[f'{self.filetype.title()}Parser'], 'tostring')(data)


class XlsxParser:
    @staticmethod
    def tostring(data: bytes):
        pure_text = ''
        sheets = pd.read_excel(data, sheet_name=None)
        for k, v in sheets.items():
            pure_text += k
            for row in v.values.tolist():
                for col in row:
                    if col is np.nan or str(col) == 'nan':
                        pure_text += ' '
                    else:
                        pure_text += str(col)
                pure_text += '\n'
        return pure_text


class DocxParser:
    @staticmethod
    def tostring(data: bytes):
        source_stream = Document(io.BytesIO(data))
        return '\n'.join([para.text for para in source_stream.paragraphs])


class TxtParser:
    pass
