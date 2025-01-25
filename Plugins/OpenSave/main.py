"""**********************************VtPlugin OpenSave***************************************
This is standart plugin to open and save files. Requires VtAPI v. 1.3

"""


from api.api2 import VtAPI

def execList(lst):
    try: return eval(lst)
    except: return []

def initAPI(api: VtAPI):
    global OpenFileCommand, SaveFileCommand, OpenRFileCommand, FileReadThread, FileWriteThread, addToRFiles, QtCore, sys, os, ast
    vtApi = api
    QtCore = vtApi.importModule("PySide6.QtCore")
    sys = vtApi.importModule("sys")
    os = vtApi.importModule("os")
    
    vtApi.activeWindow.signals.tabClosed.connect(lambda view: addToRFiles(view, VtAPI))

class OpenFileCommand(VtAPI.Plugin.WindowCommand):
    def __init__(self, api, window):
        super().__init__(api, window)
        self.api: VtAPI = api
        self.window: VtAPI.Window = window
        self.QtCore = self.api.importModule("PySide6.QtCore")
        self.chardet = self.api.importModule("chardet")
    def run(self, f: list = [], dlg=False):
        if dlg:
            f = self.api.Dialogs.openFileDialog()[0]
        # self.window.openFile(f) | Use command with name 'OpenFileCommand'
        for file in f:
            found = False
            for v in self.window.views:
                if file == v.getFile():
                    self.window.focus(v)
                    found = True
                    break
            if not found:
                view = self.window.newFile()
                view.setFile(file)
                self.window.setTitle(self.api.Path(file).normalize())
                view.setTitle(os.path.basename(file))
                self.fileReader = FileReadThread(file, self)
                self.fileReader.line_read.connect(view.insert)
                self.fileReader.start()
                self.window.signals.fileOpened.emit(view)
                view.setSaved(True)
                view.clearUndoRedoStacks()

class FileReadThread(VtAPI.Widgets.Thread):
    line_read = VtAPI.Widgets.Signal(str)
    def __init__(self, file_path: str, cclass, buffer_size: int = 1.5*1024*1024):
        super().__init__()
        self.file_path = file_path
        self.buffer_size = buffer_size
        self._is_running = True
        self.cclass: VtAPI.Plugin.WindowCommand = cclass

    def run(self):
        try:
            with open(self.file_path, 'rb') as f:
                raw_data = f.read(512)
                encoding_info = self.cclass.chardet.detect(raw_data)
                encoding = encoding_info.get('encoding', 'binary')
            f = VtAPI.File(self.file_path, encoding=encoding)
            chunks = f.read(self.buffer_size)
            stime = 1
            for i, chunk in enumerate(chunks):
                print(f"{i+1}/{len(chunks)}")
                self.line_read.emit(chunk)
                self.msleep(int(50*stime))
            self.cclass.window.activeView.setSaved(True)
            del chunks, f
        except Exception as e:
            self.cclass.api.activeWindow.setLogMsg("Error when writing file {}: {}".format(self.file_path, e))

    def stop(self):
        self._is_running = False

class SaveFileCommand(VtAPI.Plugin.WindowCommand):
    def __init__(self, api, window):
        super().__init__(api, window)
    def run(self, view=None, dlg=False):
        if not view:
            view = self.window.activeView
        if dlg or not view.getFile():
            f = self.api.Dialogs.saveFileDialog()[0]
        else:
            f = view.getFile()
        # self.window.saveFile(f) | Use command with name 'SaveFileCommand'
        text = view.getText()
        view.setFile(f)
        view.setTitle(os.path.basename(f))
        try:
            writeThread = FileWriteThread(f, text, self)
            writeThread.start()
            writeThread.wait()
            self.window.setTitle(self.api.Path(f).normalize())
            view.setSaved(True)
        except Exception as e:
            self.window.setLogMsg("Error when saving file {}: {}".format(f, e))

class FileWriteThread(VtAPI.Widgets.Thread):
    def __init__(self, file_path, content, chunk_size=1.5*1024*1024, c=None):
        super().__init__()
        self.file_path = file_path
        self.content = content
        self.chunk_size = chunk_size
        self.c = c

    def run(self):
        try:
            file = VtAPI.File(self.file_path)     
            file.write(self.content, chunk=self.chunk_size)
            self.c.setSaved(True)
        except Exception as e:
            self.c.api.activeWindow.setLogMsg("Error when writing file {}: {}".format(file.path, e))
            
class OpenRFileCommand(VtAPI.Plugin.WindowCommand):
    def __init__(self, api, window):
        super().__init__(api, window)
    def run(self):
        file = self.api.File("recent.txt")
        if not file.exists():
            file.create()
            file.write("[]")
        fList = self.api.Settings().fromFile(file).data()
        if type(fList) == list:
            if len(fList) > 0 and self.window.getCommand("OpenFileCommand"):
                self.window.runCommand({"command": "OpenFileCommand", "kwargs": {"f": [fList[-1]]}})
                fList.pop(-1)
                file.write(str(fList).replace("'", '"'))

def addToRFiles(view: VtAPI.View, api: VtAPI):
    if view.getFile():
        file = api.File("recent.txt")
        if not file.exists():
            file.create()
            file.write("[]")
        fList = api.Settings().fromFile(file).data()
        if type(fList) == list:
            fList.append(view.getFile())
        file.write(str(fList).replace("'", '"'))
