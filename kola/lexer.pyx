# distutils: sources = [kola/lex.yy.c, kola/unicode_handler.c]
cimport cython
from libc.string cimport strchr, strcmp
from cpython cimport Py_DECREF, PyLong_FromString, PyFloat_FromString, PyUnicode_FromStringAndSize, \
    PyBytes_FromStringAndSize, PyUnicode_Decode, PyErr_Format

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
    
    def __eq__(self, other):
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
    

cdef class BaseLexer(object):
    """
    KoiLang lexer reading from stdin
    """

    def __cinit__(self, *args, uint8_t stat = 0, int command_threshold = 1, **kwds):
        self.buffer = NULL
        self.lineno = 1
        self.encoding = "utf-8"
        if stat > 2:
            raise ValueError("lexer state must be between 0 and 2")
        self.stat = stat
        self.command_threshold = command_threshold
    
    def __init__(self, *, str encoding not None = "utf-8",
                 stat = None, command_threshold = None):
        if self.buffer:
            yy_delete_buffer(self.buffer)
        self._filename = "<stdin>"
        self.buffer = yy_create_buffer(stdin, BUFFER_SIZE)
        self.encoding = encoding
    
    def __dealloc__(self):
        self.close()
    
    cpdef void close(self):
        yy_delete_buffer(self.buffer)
        self.buffer = NULL
    
    cdef void set_error(self) except *:
        cdef int errno = 1
        
        # correct lineno and set error
        cdef bint c = strchr(yytext, ord('\n')) != NULL
        cdef int lineno = self.lineno
        if c or yytext[0] == 0:
            lineno -= c
            errno = 10
        kola_set_error(KoiLangSyntaxError, errno, self._filename, lineno, yytext)
    
    cdef void ensure(self):
        """
        synchronize buffer data in yylex
        """
        global yylineno
        yy_switch_to_buffer(self.buffer)
        yylineno = self.lineno
        set_stat(self.stat)
    
    cdef (int, const char*, Py_ssize_t) next_syn(self):
        self.ensure()
        cdef int syn = yylex(self.command_threshold)
        self.lineno = yylineno
        self.stat = get_stat()
        return syn, yytext, yyleng
    
    cdef Token next_token(self):
        if self.buffer == NULL:
            raise OSError("operation on closed lexer")

        cdef:
            int syn
            const char* text
            Py_ssize_t text_len
            const char* encoding
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
            val = <str>filter_text(s)
        elif syn == STRING:
            encoding = unicode2string(self.encoding, NULL)
            if strcmp(encoding, "utf-8") != 0:
                s = PyUnicode_Decode(text, text_len, encoding, NULL)
                text = unicode2string(s, &text_len)
            try:
                val = decode_escapes(text + 1, text_len - 2)
            except Exception as e:
                kola_set_errcause(KoiLangSyntaxError, 5, self._filename, self.lineno, text, e)
        elif syn == 0:
            self.set_error()
        elif syn == EOF:
            return None
        return Token(
            syn, val,
            lineno=self.lineno,
            raw_val=PyBytes_FromStringAndSize(text, text_len)
        )

    @property
    def filename(self):
        return self._filename.decode()
    
    @property
    def closed(self):
        return self.buffer == NULL
    
    def __iter__(self):
        return self
    
    def __next__(self):
        token = self.next_token()
        if token is None:
            raise StopIteration
        return token
    
    def __repr__(self):
        if self.buffer == NULL:
            return PyUnicode_FromFormat("<kola lexer in file \"%s\" closed>", self._filename, self.lineno)
        else:
            return PyUnicode_FromFormat("<kola lexer in file \"%s\" line %d>", self._filename, self.lineno)


cdef class FileLexer(BaseLexer):
    """
    KoiLang lexer reading from file
    """

    def __init__(self, __path not None, *,
                 str encoding not None = "utf-8", stat = None, command_threshold = None):
        if self.buffer:
            self.close()

        self._filenameo = __path
        cdef PyObject* p_addr
        self.fp = kola_open(__path, &p_addr, 'r')
        p = <object>p_addr
        self._filenameb = <bytes>p if isinstance(p, bytes) else (<str>p).encode()
        self._filename = self._filenameb
        Py_DECREF(p)

        self.buffer = yy_create_buffer(self.fp, BUFFER_SIZE)
        self.encoding = encoding
    
    cpdef void close(self):
        yy_delete_buffer(self.buffer)
        self.buffer = NULL
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

    def __init__(self, content not None, *,
                 str encoding not None = "utf-8", stat = None, command_threshold = None):
        if self.buffer:
            yy_delete_buffer(self.buffer)
        self._filename = "<string>"
        if isinstance(content, str):
            self.content = (<str>content).encode()
        else:
            self.content = content
        self.buffer = yy_scan_bytes(self.content, len(self.content))
        self.encoding = encoding
