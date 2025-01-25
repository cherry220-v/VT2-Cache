from api.api2 import VtAPI

def initAPI(api: VtAPI):
    global vtApi, PythonEditorCommand, jedi, QtCore, QtGui, highlighting_rules
    vtApi = api
    sys = vtApi.importModule("sys")
    os = vtApi.importModule("os")
    sys.path.insert(0, vtApi.Path.joinPath(vtApi.pluginsDir, r"PythonSyntax/Lib/site-packages"))
    QtGui = vtApi.importModule("PySide6.QtGui")
    QtCore = vtApi.importModule("PySide6.QtCore")
    import jedi

    vtApi.activeWindow.registerCommandClass({"command": PythonEditorCommand})
    vtApi.activeWindow.signals.fileOpened.connect(slot=lambda view: vtApi.activeWindow.runCommand({"command": "PythonEditorCommand"}), priority=5)
    vtApi.activeWindow.signals.textChanged.connect(textEdited, priority=1)
    multi_line_format = QtGui.QTextCharFormat()
    multi_line_format.setForeground(QtGui.QColor("gray"))
    multi_line_format.setFontItalic(True)
    highlighting_rules = {
        'keywords': {
            'pattern': [r'\b%s\b' % w for w in [
                'and', 'assert', 'break', 'class', 'continue', 'def',
                'del', 'elif', 'else', 'except', 'exec', 'finally',
                'for', 'from', 'global', 'if', 'import', 'in',
                'is', 'lambda', 'not', 'or', 'pass', 'print',
                'raise', 'return', 'try', 'while', 'yield',
                'None', 'True', 'False',
            ]],
            'color': '#C87832',  # цвет для ключевых слов
            'weight': 'bold',
        },
        'operators': {
            'pattern': [r'%s' % o for o in [
                '=', '==', '!=', '<', '<=', '>', '>=',  # Comparison
                r'\+', '-', r'\*', '/', '//', r'\%', r'\*\*',  # Arithmetic
                r'\+=', '-=', r'\*=', '/=', r'\%=',  # In-place
                r'\^', r'\|', r'\&', r'\~', r'>>', r'<<',  # Bitwise
            ]],
            'color': '#969696',  # цвет для операторов
        },
        'braces': {
            'pattern': [r'%s' % b for b in ['\{', '\}', '\(', '\)', '\[', '\]']],
            'color': '#A9A9A9',
        },
        'strings': {
            'pattern': [
                r'"[^"\\]*(\\.[^"\\]*)*"',  # Double-quoted strings
                r"'[^'\\]*(\\.[^'\\]*)*'",   # Single-quoted strings
            ],
            'color': '#146E64',  # цвет для строк
        },
        "multi_line_strings": {
            'start': r'"""',
            'end': r'"""',
            'color': '#1E786E',
        },
        'self': {
            'pattern': [r'\bself\b'],
            'color': '#96558C',  # цвет для self
            'weight': 'italic',
        },
        'defclass': {
            'pattern': [
                r'\bdef\b\s*(\w+)',  # Function definition
                r'\bclass\b\s*(\w+)',  # Class definition
            ],
            'bg': 'transparent',
            'color': '#DCDCFF',  # цвет для определения функции/класса
            'weight': 'bold',
        },
        'comments': {
            'pattern': [r'#[^\n]*'],  # Comments
            'bg': 'transparent',
            'color': '#808080',  # цвет для комментариев
        },
        'numbers': {
            'pattern': [
                r'\b[+-]?[0-9]+[lL]?\b',  # Integer literals
                r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b',  # Hexadecimal literals
                r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b',  # Float literals
            ],
            'bg': 'transparent',
            'color': '#6496BE',  # цвет для чисел
        },
    }

class PythonEditorCommand(VtAPI.Plugin.TextCommand):
    def run(self, view=None):
        if view:
            self.view = view
        if self.view.getFile() and self.view.getFile().endswith(".py"):
            self.view.setHighlighter(highlighting_rules)

def textEdited():
    if vtApi.activeWindow.activeView.getFile() and vtApi.activeWindow.activeView.getFile().endswith(".py"):
        vtApi.activeWindow.activeView.setHighlighter(highlighting_rules)
        additData = [
            {"line": 0, "pos": [0, 14], 'color': 'green', 'bg': 'black', 'weight': 'italic'},
            {"line": 1, "pos": [1, 35], 'color': 'red', 'bg': 'transparent', 'weight': 'italic'},
            {"line": 2, "pos": [0, 35], 'color': 'red', 'bg': 'transparent', 'weight': 'italic'},
        ]
        vtApi.activeWindow.activeView.setAddititionalHL(additData)
        vtApi.activeWindow.activeView.rehighlite()
        text, line, column = vtApi.activeWindow.activeView.getCompletePos()

        script = jedi.Script(text)
        try:
            completions = script.complete(line, column)
            vtApi.activeWindow.activeView.setCompleteList([completion.name for completion in completions])
        except jedi.api.exceptions._JediError:
            return
