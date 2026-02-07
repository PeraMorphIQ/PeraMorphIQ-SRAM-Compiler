# See LICENSE for licensing information.
#
# Copyright (c) 2016-2024 Regents of the University of California, Santa Cruz
# All rights reserved.
#
import re


class baseSection:
    """
    This is the base section class for other section classes to inherit.
    It is also used as the top most section.
    """
    def __init__(self):
        self.children = []

    def expand(self, dict, fd):
        for c in self.children:
            c.expand(dict, fd)


class loopSection(baseSection):
    """
    This section is for looping elements. It will repeat the children
    sections based on the key list.
    """

    def __init__(self, var, key, reverse=False):
        baseSection.__init__(self)
        self.var = var
        self.key = key
        self.reverse = reverse

    def expand(self, dict, fd):
        items = dict[self.key]
        if self.reverse:
            items = list(reversed(items))
        for ind in items:
            dict[self.var] = ind
            for c in self.children:
                c.expand(dict, fd)
        if self.var in dict:
            del dict[self.var]


class conditionalSection(baseSection):
    """
    This class will conditionally print it's children based on the 'cond'
    element.
    """
    def __init__(self, cond):
        baseSection.__init__(self)
        self.cond = cond

    def expand(self, dict, fd):
        run = eval(self.cond, dict)
        if run:
            for c in self.children:
                c.expand(dict, fd)


class textSection(baseSection):
    """
    This is plain text section. It can contain parameters that can be
    replaced based on the dictionary. Supports simple arithmetic expressions.
    """

    def __init__(self, text):
        self.text = text

    def expand(self, dict, fd):
        # Match {{ expression }} with any content inside
        varRE = re.compile(r'\{\{\s*(.+?)\s*\}\}')
        vars = varRE.finditer(self.text)
        newText = self.text
        for var in vars:
            expr = var.group(1).strip()
            original = var.group(0)
            try:
                # Try to evaluate as simple variable lookup first
                if expr in dict:
                    value = str(dict[expr])
                else:
                    # Try to evaluate as expression with dict values
                    value = str(eval(expr, {"__builtins__": {}}, dict))
            except:
                # Keep original if evaluation fails
                value = original
            newText = newText.replace(original, value)
        fd.write(newText)


class template:
    """
    The template class will read a template and generate an output file
    based on the template and the given dictionary.
    """

    def __init__(self, template, dict):
        self.template = template
        self.dict = dict

    def readTemplate(self):
        lines = []
        with open(self.template, 'r') as f:
            lines = f.readlines()

        self.baseSectionSection = baseSection()
        context = [self.baseSectionSection]
        # Updated regex to support optional | reverse filter
        forRE = re.compile(r'\s*\{% for (\S+) in (\S+)(\s*\|\s*reverse)? %\}')
        endforRE = re.compile(r'\s*\{% endfor %\}')
        ifRE = re.compile(r'\s*{% if (.*) %\}')
        endifRE = re.compile(r'\s*\{% endif %\}')
        for line in lines:
            m = forRE.match(line)
            if m:
                reverse = m.group(3) is not None
                section = loopSection(m.group(1), m.group(2), reverse=reverse)
                context[-1].children.append(section)
                context.append(section)
                continue
            m = ifRE.match(line)
            if m:
                section = conditionalSection(m.group(1))
                context[-1].children.append(section)
                context.append(section)
                continue
            if endforRE.match(line) or endifRE.match(line):
                context.pop()
            else:
                context[-1].children.append(textSection(line))

    def write(self, filename):
        fd = open(filename, 'w')
        self.readTemplate()
        self.baseSectionSection.expand(self.dict, fd)
        fd.close()
