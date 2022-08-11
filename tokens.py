import string

DIGITS = '0123456789'
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS

TKN_INT = 'INT'
TKN_FLOAT = 'FLOAT'
TKN_STRING = 'STRING'
TKN_IDENTIFIER = 'IDENTIFIER'
TKN_KEYWORD = 'KEYWORD'
TKN_PLUS = 'PLUS'
TKN_MINUS = 'MINUS'
TKN_MUL = 'MUL'
TKN_DIV = 'DIV'
TKN_POW = 'POW'
TKN_MODULO = 'MODULO'
TKN_EQ = 'EQ'
TKN_LPAREN = 'LPAREN'
TKN_RPAREN = 'RPAREN'
TKN_LSQUARE = 'LSQUARE'
TKN_RSQUARE = 'RSQUARE'
TKN_EE = 'EE'
TKN_NE = 'NE'
TKN_LT = 'LT'
TKN_GT = 'GT'
TKN_LTE = 'LTE'
TKN_GTE = 'GTE'
TKN_COMMA = 'COMMA'
TKN_ARROW = 'ARROW'
TKN_NEWLINE = 'NEWLINE'
TKN_EOF = 'EOF'

KEYWORDS = [ 'let', 'and', 'or', 'not', 'if', 'consider', 'last', 'for', 
'to', 'change', 'while', 'func', 'do', 'end', 
'return', 'continue', 'break' ]

class Token:
  def __init__(self, typ, value=None, start=None, end=None):
    self.type = typ
    self.value = value

    if start:
      self.start = start.copy()
      self.end = start.copy()
      self.end.next()

    if end:
      self.end = end.copy()

  def matches(self, typ, value):
    return self.type == typ and self.value == value
  
  def __repr__(self):
    if self.value: return f'{self.type}:{self.value}'
    return f'{self.type}'

class Position:
  def __init__(self, index, line, col, fn, ftxt):
    self.index = index
    self.line = line
    self.col = col
    self.fn = fn
    self.ftxt = ftxt

  def next(self, current_char=None):
    self.index += 1
    self.col += 1

    if current_char == '\n':
      self.line += 1
      self.col = 0

    return self

  def copy(self):
    return Position(self.index, self.line, self.col, self.fn, self.ftxt)