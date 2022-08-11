def arrow_error_indicator(text, start, end):
    arrows = ''

    # Calculate indices
    index_start = max(text.rfind('\n', 0, start.index), 0)
    index_end = text.find('\n', index_start + 1)
    if index_end < 0: index_end = len(text)
    
    # Generate each line
    line_count = end.line - start.line + 1
    for i in range(line_count):
        # Calculate line columns
        line = text[index_start:index_end]
        col_start = start.col if i == 0 else 0
        col_end = end.col if i == line_count - 1 else len(line) - 1

        # Append to the result
        arrows += line + '\n'
        arrows += ' ' * col_start + '^' * (col_end - col_start)

        # Re-calculate indices
        index_start = index_end
        index_end = text.find('\n', index_start + 1)
        if index_end < 0: index_end = len(text)

    return arrows.replace('\t', '')