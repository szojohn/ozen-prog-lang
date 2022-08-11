class NumberNode:
  def __init__(self, tkn):
    self.tkn = tkn

    self.start = self.tkn.start
    self.end = self.tkn.end

  def __repr__(self):
    return f'{self.tkn}'

class StringNode:
  def __init__(self, tkn):
    self.tkn = tkn

    self.start = self.tkn.start
    self.end = self.tkn.end

  def __repr__(self):
    return f'{self.tkn}'

class ListNode:
  def __init__(self, element_nodes, start, end):
    self.element_nodes = element_nodes

    self.start = start
    self.end = end

class VarAccessNode:
  def __init__(self, var_name_tkn):
    self.var_name_tkn = var_name_tkn

    self.start = self.var_name_tkn.start
    self.end = self.var_name_tkn.end

class VarAssignNode:
  def __init__(self, var_name_tkn, value_node):
    self.var_name_tkn = var_name_tkn
    self.value_node = value_node

    self.start = self.var_name_tkn.start
    self.end = self.value_node.end

class BinOpNode:
  def __init__(self, left_node, op_tkn, right_node):
    self.left_node = left_node
    self.op_tkn = op_tkn
    self.right_node = right_node

    self.start = self.left_node.start
    self.end = self.right_node.end

  def __repr__(self):
    return f'({self.left_node}, {self.op_tkn}, {self.right_node})'

class UnaryOpNode:
  def __init__(self, op_tkn, node):
    self.op_tkn = op_tkn
    self.node = node

    self.start = self.op_tkn.start
    self.end = node.end

  def __repr__(self):
    return f'({self.op_tkn}, {self.node})'

class IfNode:
  def __init__(self, cases, else_case):
    self.cases = cases
    self.else_case = else_case

    self.start = self.cases[0][0].start
    self.end = (self.else_case or self.cases[len(self.cases) - 1])[0].end

class ForNode:
  def __init__(self, var_name_tkn, start_value_node, end_value_node, step_value_node, body_node, should_return_null):
    self.var_name_tkn = var_name_tkn
    self.start_value_node = start_value_node
    self.end_value_node = end_value_node
    self.step_value_node = step_value_node
    self.body_node = body_node
    self.should_return_null = should_return_null

    self.start = self.var_name_tkn.start
    self.end = self.body_node.end

class WhileNode:
  def __init__(self, condition_node, body_node, should_return_null):
    self.condition_node = condition_node
    self.body_node = body_node
    self.should_return_null = should_return_null

    self.start = self.condition_node.start
    self.end = self.body_node.end

class FuncDefNode:
  def __init__(self, var_name_tkn, arg_name_tkns, body_node, should_auto_return):
    self.var_name_tkn = var_name_tkn
    self.arg_name_tkns = arg_name_tkns
    self.body_node = body_node
    self.should_auto_return = should_auto_return

    if self.var_name_tkn:
      self.start = self.var_name_tkn.start
    elif len(self.arg_name_tkns) > 0:
      self.start = self.arg_name_tkns[0].start
    else:
      self.start = self.body_node.start

    self.end = self.body_node.end

class CallNode:
  def __init__(self, node_to_call, arg_nodes):
    self.node_to_call = node_to_call
    self.arg_nodes = arg_nodes

    self.start = self.node_to_call.start

    if len(self.arg_nodes) > 0:
      self.end = self.arg_nodes[len(self.arg_nodes) - 1].end
    else:
      self.end = self.node_to_call.end

class ReturnNode:
  def __init__(self, node_to_return, start, end):
    self.node_to_return = node_to_return

    self.start = start
    self.end = end

class ContinueNode:
  def __init__(self, start, end):
    self.start = start
    self.end = end

class BreakNode:
  def __init__(self, start, end):
    self.start = start
    self.end = end