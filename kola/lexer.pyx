# distutils: sources = [kola/unicode_handler.c]
cimport cython
from libc.stdint cimport uint8_t
from libc.string cimport strchr, strcmp
from cpython cimport Py_DECREF, PyLong_FromString, PyFloat_FromString, PyBytes_FromStringAndSize
from cpython.unicode cimport PyUnicode_FromStringAndSize, PyUnicode_Decode
from cpython.exc cimport PyErr_Format, PyErr_SetFromErrno
from cpython.object cimport PyTypeObject
from cpython.type cimport PyType_Modified
from ._yylex cimport *

from .exception import KoiLangSyntaxError


DEF BUFFER_SIZE = 1 << 14

# token syn
S_CMD = CMD
S_CMD_N = CMD_N
S_TEXT = TEXT
S_LITERAL = LITERAL
S_STRING = STRING
S_NUM = NUM
S_NUM_H = NUM_H
S_NUM_B = NUM_B
S_NUM_F = NUM_F
S_CLN = CLN
S_CMA = CMA
S_SLP = SLP
S_SRP = SRP
S_ANNOTATION = ANNOTATION
F_DISABLED = LFLAG_DISABLED
F_LSTRIP_TEXT = LFLAG_NOLSTRIP


@cython.final
cdef class Token:
    """
    Token used in lexer

    Don't instantiate this class directly unless you make
    sure enough arguments provided.
    """

    def __cinit__(
        self,
        TokenSyn syn,
        val = None,
        *,
        int lineno = 0,
        bytes raw_val = None
    ):
        self.syn = syn
        self.val = val

        self.lineno = lineno
        self.raw_val = bytes(val) if raw_val is None else raw_val
    
    def __eq__(self, other) -> bool:
        return self is other or self.syn == other
    
    cpdef int get_flag(self):
        if self.syn <= TEXT or self.syn == ANNOTATION:
            return 0
        elif self.syn == LITERAL:
            return 1
        elif self.syn <= NUM_F:
            return 2
        else:
            return self.syn - CLN + 3 
    
    def __repr__(self):
        if self.val is None:
            return PyUnicode_FromFormat("<token %d>", self.syn)
        else:
            return PyUnicode_FromFormat("<token %d: %R>", self.syn, <void*>self.val)


cdef class LexerConfig:
    """
    Python-level interface to access extra lexer data
    """

    def __init__(self, BaseLexer lexer not None):
        self.lexer = lexer
        self.lexer_data = &lexer.lexer_data
    
    def dict(self) -> dict:
        cdef dict data = {}
        for i in _lexer_data_names:
            data[i] = getattr(self, <str>i)
        return data
    
    def set(self, **kwds) -> None:
        for k, v in kwds.items():
            if not k in _lexer_data_names:
                PyErr_Format(AttributeError, "invalid config item '%U'", <void*>k)
            setattr(self, k, v)
    
    @property
    def filename(self) -> str:
        return self.lexer_data.filename.decode()
    
    @property
    def encoding(self) -> str:
        return self.lexer.encoding
    
    @encoding.setter
    def encoding(self, val: str) -> None:
        self.lexer.encoding = val
    
    @property
    def command_threshold(self) -> int:
        return self.lexer_data.command_threshold
    
    @command_threshold.setter
    def command_threshold(self, uint8_t cmd_threshold) -> None:
        self.lexer_data.command_threshold = cmd_threshold
    
    @property
    def flag(self) -> int:
        return self.lexer_data.flag
    
    @flag.setter
    def flag(self, uint8_t val) -> None:
        self.lexer_data.flag = val
    
    @property
    def disabled(self) -> bool:
        return True if self.lexer_data.flag & LFLAG_DISABLED else False
    
    @disabled.setter
    def disabled(self, val: bool) -> None:
        if val:
            self.lexer_data.flag |= LFLAG_DISABLED
        else:
            self.lexer_data.flag &= ~LFLAG_DISABLED
            
    @property
    def no_lstrip(self) -> bool:
        return True if self.lexer_data.flag & LFLAG_NOLSTRIP else False
    
    @no_lstrip.setter
    def no_lstrip(self, val: bool) -> None:
        if val:
            self.lexer_data.flag |= LFLAG_NOLSTRIP
        else:
            self.lexer_data.flag &= ~LFLAG_NOLSTRIP


cdef set _lexer_data_names = {
    i for i in dir(LexerConfig)
    if not (<str>i).startswith('__') and not (<str>i).endswith('__') and PyDescr_IsData(getattr(LexerConfig, (<str>i)))
}

# update LexerConfig.attr_names
(<dict>(<PyTypeObject*>LexerConfig).tp_dict)["data_names"] = frozenset(_lexer_data_names)
PyType_Modified(LexerConfig)


cdef class BaseLexer(object):
    """
    KoiLang lexer reading from stdin
    """

    def __cinit__(self, *args, **kwds):
        self.encoding = "utf-8"
        self.lexer_data.filename = "<kolafile>"
        self.lexer_data.command_threshold = 1
        if yylex_init_extra(&self.lexer_data, &self.scanner):
            PyErr_SetFromErrno(RuntimeError)
    
    def __init__(self, **kwds):
        yyrestart(stdin, self.scanner)
        self.lexer_data.filename = "<stdin>"
        LexerConfig(self).set(**kwds)
    
    def __dealloc__(self):
        self.close()
        if self.scanner:
            yylex_destroy(self.scanner)
    
    cpdef void close(self):
        yypop_buffer_state(self.scanner)
    
    cdef void set_error(self, const char* text) except *:
        cdef int errno = 1
        
        # correct lineno and set error
        cdef bint c = strchr(text, ord('\n')) != NULL
        cdef int lineno = yyget_lineno(self.scanner)
        if c or text[0] == 0:
            lineno -= c
            errno = 10
        kola_set_error(KoiLangSyntaxError, errno, self.lexer_data.filename, lineno, text)
    
    cdef (int, const char*, Py_ssize_t) next_syn(self) nogil:
        cdef int syn = yylex(self.scanner)
        return syn, yyget_text(self.scanner), yyget_leng(self.scanner)
    
    cdef Token next_token(self):
        if not yylex_check(self.scanner):
            raise OSError("operation on closed lexer")

        cdef:
            int syn
            const char* text
            Py_ssize_t text_len
            const char* encoding
        with nogil:
            syn, text, text_len = self.next_syn()

        val = None
        if syn == NUM or syn == CMD_N:
            val = PyLong_FromString(text, NULL, 10)
        elif syn == NUM_H:
            val = PyLong_FromString(text, NULL, 16)
        elif syn == NUM_B:
            val = PyLong_FromString(text, NULL, 2)
        elif syn == NUM_F:
            val = PyFloat_FromString(text)
        elif syn == CMD or syn == LITERAL:
            val = PyUnicode_FromStringAndSize(text, text_len)
        elif syn == TEXT or syn == ANNOTATION:
            encoding = unicode2string(self.encoding, NULL)
            s = PyUnicode_Decode(text, text_len, encoding, NULL)
            val = filter_text(s)
        elif syn == STRING:
            encoding = unicode2string(self.encoding, NULL)
            if strcmp(encoding, "utf-8") != 0:
                s = PyUnicode_Decode(text, text_len, encoding, NULL)
                text = unicode2string(s, &text_len)
            try:
                val = decode_escapes(text + 1, text_len - 2)
            except Exception as e:
                kola_set_errcause(KoiLangSyntaxError, 5, self.lexer_data.filename, yyget_lineno(self.scanner), text, e)
        elif syn == 0:
            self.set_error(text)
        elif syn == EOF:
            return None
        return Token(
            syn, val,
            lineno=yyget_lineno(self.scanner),
            raw_val=PyBytes_FromStringAndSize(text, text_len)
        )

    @property
    def filename(self):
        return self.lexer_data.filename.decode()
    
    @property
    def lineno(self):
        return yyget_lineno(self.scanner)
    
    @property
    def column(self):
        return yyget_column(self.scanner)
    
    @property
    def config(self) -> LexerConfig:
        return LexerConfig(self)
    
    @property
    def closed(self) -> bool:
        return not yylex_check(self.scanner)
    
    def __iter__(self):
        return self
    
    def __next__(self):
        token = self.next_token()
        if token is None:
            raise StopIteration
        return token
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    def __repr__(self):
        if not yylex_check(self.scanner):
            return PyUnicode_FromFormat(
                "<kola lexer in file \"%s\" closed>",
                self.lexer_data.filename
            )
        else:
            return PyUnicode_FromFormat(
                "<kola lexer in file \"%s\" line %d>",
                self.lexer_data.filename,
                yyget_lineno(self.scanner)
            )


cdef class FileLexer(BaseLexer):
    """
    KoiLang lexer reading from file
    """

    def __init__(self, __path not None, **kwds):
        if self.fp:
            fclose(self.fp)

        self._filenameo = __path
        cdef PyObject* p_addr
        self.fp = kola_open(__path, &p_addr, 'r')
        p = <object>p_addr
        self._filenameb = <bytes>p if isinstance(p, bytes) else (<str>p).encode()
        Py_DECREF(p)

        yyrestart(self.fp, self.scanner)
        self.lexer_data.filename = self._filenameb
        LexerConfig(self).set(**kwds)
    
    cpdef void close(self):
        BaseLexer.close(self)
        if self.fp:
            fclose(self.fp)
            self.fp = NULL
    
    @property
    def filename(self):
        return self._filenameo


cdef class StringLexer(BaseLexer):
    """
    KoiLang lexer reading from string provided
    """

    def __init__(self, content: Union[str, bytes], **kwds):
        if not self.content is None:
            yypop_buffer_state(self.scanner)

        if isinstance(content, str):
            self.content = (<str>content).encode()
        else:
            self.content = content

        yy_scan_bytes(self.content, len(self.content), self.scanner)
        self.lexer_data.filename = "<string>"
        LexerConfig(self).set(**kwds)
