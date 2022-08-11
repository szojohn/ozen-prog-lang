from arrow_error_indicator import *

class Error:
  def __init__(self, start, end, error_name, details):
    self.start = start
    self.end = end
    self.error_name = error_name
    self.details = details
  
  def arrow_string(self):
    result  = f'{self.error_name}: {self.details}\n'
    result += f'File {self.start.fn}, line {self.start.line + 1}'
    result += '\n\n' + arrow_error_indicator(self.start.ftxt, self.start, self.end)
    return result

class IllegalCharError(Error):
  def __init__(self, start, end, details):
    super().__init__(start, end, 'Illegal Character', details)

class ExpectedCharError(Error):
  def __init__(self, start, end, details):
    super().__init__(start, end, 'Expected Character', details)

class InvalidSyntaxError(Error):
  def __init__(self, start, end, details=''):
    super().__init__(start, end, 'Invalid Syntax', details)

class RunTimeError(Error):
  def __init__(self, start, end, details, context):
    super().__init__(start, end, 'Runtime Error', details)
    self.context = context

  def arrow_string(self):
    result  = self.generate_traceback()
    result += f'{self.error_name}: {self.details}'
    result += '\n\n' + arrow_error_indicator(self.start.ftxt, self.start, self.end)
    return result

  def generate_traceback(self):
    result = ''
    pos = self.start
    ctx = self.context

    while ctx:
      result = f'  File {pos.fn}, line {str(pos.line + 1)}, in {ctx.display_name}\n' + result
      pos = ctx.parent_entry_pos
      ctx = ctx.parent

    return 'Traceback (most recent call last):\n' + result