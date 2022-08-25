from .exception import KoiLangSyntaxError


cdef class Parser:
    def __init__(self, BaseLexer lexer not None, command_set not None):
        self.lexer = lexer
        self.command_set = command_set
    
    cpdef void push(self, Token n):
        n.next = self.stack_top
        self.stack_top = n
    
    cpdef Token pop(self):
        cdef Token n = self.stack_top
        if n is None:
            self.set_error(210)
        self.stack_top = n.next
        return n
    
    cdef void set_error(self, int errorno = 16) except *:
        cdef:
            int lineno = 1
            const char* text = ""
        if not self.t_cache is None:
            lineno = self.t_cache.lineno
            if errorno == 16:
                errorno = (self.stat << 4) + self.t_cache.syn
            text = <char*>self.t_cache.raw_val
        while not self.t_cache is None and not CMD <= self.t_cache.syn <= TEXT:
            self.t_cache = self.lexer.next_token()
        kola_set_error(KoiLangSyntaxError, errorno,
            self.lexer._filename, lineno, text)
    
    cpdef object exec_once(self):
        cdef:
            uint8_t stat = 1, action = 0

            list args = []
            dict kwds = {}
            object v
            Token i

        i = self.t_cache
        if i is None:
            i = self.lexer.next_token()
            if i is None:
                self.stat = 255
                return
        if i.syn == CMD:
            c = self.command_set[i.val]
        elif i.syn == CMD_N:
            c = self.command_set["@number"]
            args.append(i.val)
        elif i.syn == TEXT:
            c = self.command_set["@text"]
            args.append(i.val)
        
        while True:
            self.stat = stat
            i = self.lexer.next_token()
            if i is None:
                break
                
            stat = yy_goto[i.get_flag()][stat - 1]
            action = stat >> 4
            stat &= 0x0F

            if action == 1:
                args.append(i.val)
            elif action == 2:
                self.push(i)
            elif action == 3:
                args.append(self.pop().val)
            elif action == 4:
                v = self.pop().val
                i = self.pop()
                if not i.syn == LITERAL:
                    self.t_cache = i
                    self.set_error(201)
                kwds[i.val] = v
            elif action == 5:
                i = self.pop()
                if not i.syn == LITERAL:
                    self.t_cache = i
                    self.set_error(202)
                kwds[i.val] = v
            elif action == 6:
                v = [self.pop().val]
            elif action == 7:
                (<list>v).append(i.val)
            elif action == 8:
                v = {}
            elif action == 9:
                (<dict>v)[self.pop().val] = i.val
            elif action == 10:
                args.append(self.pop().val)
                self.push(i)

            if stat == 15:
                break
            elif stat == 0:
                self.t_cache = i
                self.set_error()
                
        if not self.stack_top is None:
            self.t_cache = self.stack_top
            self.stack_top = None
            self.set_error()

        self.t_cache = i
        return c(*args, **kwds)
    
    cpdef void exec_(self) except *:
        self.exec_once()
        while not self.t_cache is None:
            self.exec_once()

    def __iter__(self):
        return self
    
    def __next__(self):
        ret = self.exec_once()
        if self.stat == 255:
            raise StopIteration
        return ret
    
    def __repr__(self):
        return PyUnicode_FromFormat("<kola parser in file \"%s\">", self.lexer._filename)