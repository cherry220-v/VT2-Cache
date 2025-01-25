"""**********************************VtPlugin OpenSave***************************************
This is standart Basic plugin with VT2 functions. You can edit/rewrite functions as you like. Requires vtApi v. 1.3

"""

from api.api2 import VtAPI

def initAPI(api: VtAPI):
    global vtApi, os, shutil, zipfile, uuid, json, req, re, err, QtWidgets, QtCore, QtGui, msgpack
    vtApi = api
    shutil = vtApi.importModule("shutil")
    zipfile = vtApi.importModule("zipfile")
    uuid = vtApi.importModule("uuid")
    json = vtApi.importModule("json")
    req = vtApi.importModule("urllib.request")
    re = vtApi.importModule("re")
    err = vtApi.importModule("urllib.error")
    QtWidgets = vtApi.importModule("PySide6.QtWidgets")
    QtGui = vtApi.importModule("PySide6.QtGui")
    QtCore = vtApi.importModule("PySide6.QtCore")
    msgpack = vtApi.importModule("msgpack")

    window: VtAPI.Window = vtApi.activeWindow

    window.registerCommandClass({"command": SetThemeCommand})
    window.registerCommandClass({"command": ShowHideMinimap})
    window.registerCommandClass({"command": InitFileTagsCommand})
    window.registerCommandClass({"command": GetFilesForTagCommand})
    window.registerCommandClass({"command": AddTagCommand, "shortcut": "ctrl+f"})
    window.registerCommandClass({"command": RemoveTagCommand})

    window.signals.tabChanged.connect(mMapActionUpdate)
    window.signals.windowStateRestoring.connect(restoreWState, priority=10)
    window.signals.windowStateRestoring.connect(restoreConsoleState)
    window.signals.windowStateSaving.connect(saveWState, priority=10)
    window.signals.windowStateSaving.connect(saveConsoleState)
    window.signals.fileOpened.connect(lambda: window.runCommand({"command": "InitFileTagsCommand", "kwargs": {"view": window.activeView}}))
    window.signals.windowStarted.connect(loadThemes)

class CommandParser:
    def __init__(self, window):
        self.window = window
        self.api = window.api
        self.signal_activate_pattern = r'^signal:activate (?P<signal_name>\w+)\[(?P<data>.+?)\]$'
        self.signal_exists_pattern = r'^signal:exists (?P<signal_name>\w+)$'
        
        self.command_exists_pattern = r'^command:exists (?P<command_name>\w+)$'
        self.command_run_pattern1 = r'^command:run (?P<command_name>\w+)$'
        self.command_run_pattern2 = r'^command:run (?P<command_name>\w+)\[(?P<data>.+?)\]$'

        self.api_version_pattern = r'^api:version$'
        self.api_command_pattern1 = r'^api:command (?P<command_name>\w+)$'
        self.api_command_pattern2 = r'^api:command (?P<command_name>\w+)\[(?P<data>.+?)\]$'

    def parse(self, input_line):
        patterns = [
            (self.signal_activate_pattern, self.handle_signal_activate),
            (self.signal_exists_pattern, self.handle_signal_exists),
            (self.command_exists_pattern, self.handle_command_exists),
            (self.command_run_pattern1, self.handle_command_run),
            (self.command_run_pattern2, self.handle_command_run),
            (self.api_version_pattern, self.handle_api_version),
            (self.api_command_pattern1, self.handle_api_command),
            (self.api_command_pattern2, self.handle_api_command),
        ]
        
        for pattern, handler in patterns:
            match = re.match(pattern, input_line)
            if match:
                try:
                    handler(match)
                except Exception as e:
                    self.window.setLogMsg(e)
                return
        else: raise SyntaxError("Invalid console syntax")

    def handle_signal_activate(self, match):
        signal_name = match.group('signal_name')
        data = match.group('data')
        print(f"Activating signal '{signal_name}' with data: {data}")

    def handle_signal_exists(self, match):
        signal_name = match.group('signal_name')
        self.window.setLogMsg(self.window.signals.findSignal(signal_name))

    def handle_command_exists(self, match):
        command_name = match.group('command_name')
        self.window.setLogMsg(self.window.getCommand(command_name))

    def handle_command_run(self, match):
        command_name = match.group('command_name')
        command = {"command": command_name}
        try:
            data = match.group('data')
            if type(data) == dict: t = "kwargs"
            else: t = "args"
            command[t] = data
        except: data = None
        self.window.runCommand(command)

    def handle_api_version(self, match):
        self.window.setLogMsg(f"**vtApi v. {self.api.version()}**")

    def handle_api_command(self, match):
        command_name = match.group('command_name')
        try:
            data = match.group('data')
            data = [data]
        except: data = []
        if hasattr(self.api, command_name):
            out = getattr(self.api, command_name)(*data)
            self.window.setLogMsg(str(out))

class LogConsoleCommand(VtAPI.Plugin.WindowCommand):
    def __init__(self, api: VtAPI, window):
        self.api: VtAPI = api
        self.window: VtAPI.Window = window
        super().__init__(api, window)
        self.createWidget()
    def run(self, restoring=False, state=None):
        if not restoring:
            if self.api.findKey("state.logConsole.active", self.api.STATEFILE.get(vtApi.activeWindow.id)):
                self.console = self.window.isDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea)
                self.console.deleteLater()
                self.api.addKey("state.logConsole.active", False, self.api.STATEFILE.get(self.window.id))
            else:
                self.console = ConsoleWidget(self.window, self.api)
                self.console.textEdit.append(self.window.getLog())
                self.window.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self.console)
                self.api.addKey("state.logConsole.active", True, self.api.STATEFILE.get(self.window.id))
        else:
            if state:
                self.console = ConsoleWidget(self.window, self.api)
                self.console.textEdit.append(self.window.getLog())
                self.window.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self.console)
                self.api.addKey("state.logConsole.active", True, self.api.STATEFILE.get(self.window.id))
    def createWidget(self):
        global ConsoleWidget
        class ConsoleWidget(vtApi.Widgets.DockWidget):
            def __init__(self, window: VtAPI.Window, api):
                super().__init__()
                self.api: VtAPI = api
                self.window: VtAPI.Window = window
                self.parser = CommandParser(self.window)
                self.setWindowTitle(self.api.appName+" - Console")
                self.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable)
                self.setAllowedAreas(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea)
                self.consoleWidget = QtWidgets.QWidget()
                self.consoleWidget.setObjectName("consoleWidget")
                self.verticalLayout = QtWidgets.QVBoxLayout(self.consoleWidget)
                self.verticalLayout.setObjectName("verticalLayout")
                self.textEdit = QtWidgets.QTextEdit(parent=self.consoleWidget)
                self.textEdit.setReadOnly(True)
                self.textEdit.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.NoTextInteraction)
                self.textEdit.setObjectName("consoleOutput")
                self.verticalLayout.addWidget(self.textEdit)
                self.lineEdit = QtWidgets.QLineEdit(parent=self.consoleWidget)
                self.lineEdit.setMouseTracking(False)
                self.lineEdit.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
                self.lineEdit.setCursorMoveStyle(QtCore.Qt.CursorMoveStyle.LogicalMoveStyle)
                self.lineEdit.setObjectName("consoleCommandLine")
                self.verticalLayout.addWidget(self.lineEdit)
                self.setWidget(self.consoleWidget)
                self.lineEdit.returnPressed.connect(self.sendCommand)
                self.window.signals.logWrited.connect(self.updateLog)
            def updateLog(self, value):
                try:
                    self.textEdit.clear()
                    self.textEdit.textCursor().insertHtml(f"<br>{value}")
                    scrollbar = self.textEdit.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
                except RuntimeError: pass
            def sendCommand(self):
                text = self.lineEdit.text()
                if text:
                    try:
                        self.parser.parse(text)
                    except: self.window.setLogMsg("Invalid console syntax", self.api.ERROR)
                    self.lineEdit.clear()
            def closeEvent(self, e):
                self.api.activeWindow.runCommand({"command": "LogConsoleCommand"})
                e.ignore()

class NewTabCommand(VtAPI.Plugin.WindowCommand):
    def __init__(self, api, window):
        super().__init__(api, window)
        self.api: VtAPI
        self.window: VtAPI.Window
    def run(self):
        self.window.newFile()
        self.window.activeView.setTitle("Untitled")

class SelectAllCommand(VtAPI.Plugin.TextCommand):
    def __init__(self, api, view):
        super().__init__(api, view)
        self.api: VtAPI
        self.view: VtAPI.View
    def run(self):
        self.view.selectAll()

class CopyCommand(VtAPI.Plugin.TextCommand):
    def __init__(self, api, view):
        super().__init__(api, view)
        self.api: VtAPI
        self.view: VtAPI.View
    def run(self):
        self.view.copy()

class PasteCommand(VtAPI.Plugin.TextCommand):
    def __init__(self, api, view):
        super().__init__(api, view)
        self.api: VtAPI
        self.view: VtAPI.View
    def run(self):
        cb = QtGui.QGuiApplication.clipboard()
        self.view.insert(cb.text())

class CutCommand(VtAPI.Plugin.TextCommand):
    def __init__(self, api, view):
        super().__init__(api, view)
        self.api: VtAPI
        self.view: VtAPI.View
    def run(self):
        self.view.cut()

class UndoCommand(VtAPI.Plugin.TextCommand):
    def __init__(self, api, view):
        super().__init__(api, view)
        self.api: VtAPI
        self.view: VtAPI.View
    def run(self):
        self.view.undo()

class RedoCommand(VtAPI.Plugin.TextCommand):
    def __init__(self, api, view):
        super().__init__(api, view)
        self.api: VtAPI
        self.view: VtAPI.View
    def run(self):
        self.view.redo()

class SetThemeCommand(VtAPI.Plugin.WindowCommand):
    def __init__(self, api, window):
        super().__init__(api, window)
        self.api: VtAPI
        self.window: VtAPI.Window
    def run(self, theme):
        self.window.setTheme(theme)

class ShowPMCommand(VtAPI.Plugin.WindowCommand):
    def __init__(self, api, window):
        super().__init__(api, window)
        self.api: VtAPI
        self.window: VtAPI.Window
    def run(self):
        mLayout = self.constructWindow(self.api.packagesDirs)
        try:
            self.updateRepos()
        except err.URLError:
            self.window.setLogMsg("Repo service unaviable. Try again later")
        except Exception as e:
            self.window.setLogMsg("Error when updating repos. {}".format(e))
            
        self.processPlugins()
        self.processThemes()

        self.window.showDialog(content=mLayout, width=800, height=600)
    def constructWindow(self, packagesDir):
        self.packagesDir = packagesDir
        self.tempDir = vtApi.replacePaths("%TEMP%")

        self.mainLayout = QtWidgets.QVBoxLayout()

        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self.tabWidget.setObjectName("tabWidget")

        self.createPluginTab()
        self.createThemeTab()

        self.tabWidget.addTab(self.pluginTab, "Plugins")
        self.tabWidget.addTab(self.themeTab, "Themes")
        self.mainLayout.addWidget(self.tabWidget)
        return self.mainLayout

    def createPluginTab(self):
        self.pluginTab = QtWidgets.QWidget()
        self.l = QtWidgets.QVBoxLayout(self.pluginTab)
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.l.addWidget(self.scrollArea)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.scrollAreaLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        return self.pluginTab

    def createThemeTab(self):
        self.themeTab = QtWidgets.QWidget()
        self.l2 = QtWidgets.QVBoxLayout(self.themeTab)
        self.scrollArea2 = QtWidgets.QScrollArea()
        self.scrollArea2.setWidgetResizable(True)
        self.scrollAreaWidgetContents2 = QtWidgets.QWidget()
        self.l2.addWidget(self.scrollArea2)
        self.scrollArea2.setWidget(self.scrollAreaWidgetContents2)
        self.scrollAreaLayout2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents2)
        return self.themeTab

    def addCard(self, l, c, url, name, type):
        widget = QtWidgets.QWidget(parent=c)
        widget.setMaximumSize(QtCore.QSize(16777215, 100))
        cardLayout = QtWidgets.QHBoxLayout(widget)

        cardTextLayout = QtWidgets.QVBoxLayout()
        nameLbl = QtWidgets.QLabel(name)
        repoLbl = QtWidgets.QLabel(f"<html><head/><body><p><span style=\" font-weight:600; font-style:italic; color:#383838;\">{url}</span></p></body></html>")
        descriptLbl = QtWidgets.QLabel("This is a description of the Plugin")

        cardTextLayout.addWidget(nameLbl)
        cardTextLayout.addWidget(repoLbl)
        cardTextLayout.addWidget(descriptLbl)
        
        cardLayout.addLayout(cardTextLayout)

        pushButton = QtWidgets.QPushButton("Download", parent=widget)
        pushButton.clicked.connect(lambda: self.install(url, type=type))
        cardLayout.addWidget(pushButton)

        l.addWidget(widget)

    def install(self, url, site="github", type="plugin"):
        try:
            tempdirName = self.tempname(8)
            path = vtApi.Path.joinPath(self.tempDir or vtApi.Path(__file__).dirName(), tempdirName)
            vtApi.Path(path).create()

            filePath = vtApi.Path.joinPath(path, "package.zip")
            if site == "github":
                req.urlretrieve(url + "/zipball/master", filePath)
            else:
                req.urlretrieve(url, filePath)

            with zipfile.ZipFile(filePath, 'r') as f:
                f.extractall(path)
            vtApi.Path(filePath).remove()

            extracted_dir = next(
                vtApi.Path.joinPath(path, d) for d in vtApi.Path(path).dir()
                if vtApi.Path(vtApi.Path.joinPath(path, d)).isDir()
            )
            if type == "plugin":
                finalPackageDir = vtApi.Path.joinPath(self.packagesDir, "Plugins", url.split("/")[-1])
            else:
                finalPackageDir = vtApi.Path.joinPath(self.packagesDir, "Themes", url.split("/")[-1])
            vtApi.Path(self.packagesDir).create()

            shutil.move(extracted_dir, finalPackageDir)
            shutil.rmtree(path)

            self.checkReqs(finalPackageDir)
        except Exception as e:
            self.window.setLogMsg(f"Error when loading plugin from '{url}'", self.__windowApi.ERROR)

    def tempname(self, n):
        return "vt-" + str(uuid.uuid4())[:n + 1] + "-install"

    def installModule(self, packages: str):
        import pip
        pip.main(["install", packages])

    def checkReqs(self, data):
        for url in data:
            if not vtApi.Path(vtApi.Path.joinPath(self.packagesDir, url.split("/")[-1])).isDir():
                self.install(url)

    def uninstall(self, name):
        dir_path = vtApi.Path.joinPath(self.packagesDir, name)
        if vtApi.Path(dir_path).isDir():
            shutil.rmtree(dir_path)

    def search(self, type: str, name):
        dir_path = vtApi.Path.joinPath(self.packagesDir, type.title(), name)
        return dir_path if vtApi.Path(dir_path).isDir() else ""

    def updateRepos(self):
        update_url = "http://127.0.0.1:8000/update"
        zip_path = vtApi.Path.joinPath(self.api.cacheDir, "plugins.zip")
        req.urlretrieve(update_url, zip_path)

        with zipfile.ZipFile(zip_path, 'r') as f:
            f.extractall(self.api.cacheDir)
        vtApi.Path(zip_path).remove()

    def processPlugins(self):
        plugins_dir = vtApi.Path.joinPath(self.api.cacheDir, "plugins")
        if not vtApi.Path(plugins_dir).isDir(): vtApi.Path(plugins_dir).create()
        for pl in vtApi.Path(plugins_dir).dir():
            with open(vtApi.Path.joinPath(plugins_dir, pl), "r") as f:
                try:
                    data = json.load(f)
                    if all(k in data for k in ("apiVersion", "repo", "name")):
                        if "platform" in data and self.api.platform() not in data["platform"]:
                            continue
                        if "requirements" in data:
                            try: self.checkReqs(data["requirements"])
                            except: pass
                        if "modules" in data:
                            try: self.installModule(" ".join(data["modules"]))
                            except: pass
                        self.addCard(self.scrollAreaLayout, self.scrollAreaWidgetContents, data["repo"], name=data["name"], type="plugin")            
                except Exception as e:
                    self.window.setLogMsg(f"Error processing plugin {pl}: {e}")

    def processThemes(self):
        themes_dir = vtApi.Path.joinPath(self.api.cacheDir, "themes")
        if not vtApi.Path(themes_dir).isDir(): vtApi.Path(themes_dir).create()
        for th in vtApi.Path(themes_dir).dir():
            with open(vtApi.Path.joinPath(themes_dir, th), "r") as f:
                try:
                    data = json.load(f)
                    if all(k in data for k in ("repo", "name")): 
                        self.addCard(self.scrollAreaLayout2, self.scrollAreaWidgetContents2, data["repo"], name=data["name"], type="theme")            
                except Exception as e:
                    self.window.setLogMsg(f"Error processing theme {th}: {e}")

class CloseTabCommand(VtAPI.Plugin.WindowCommand):
    def run(self, view=None):
        if not view:
            view = self.window.activeView
        for v in self.window.views:
            if v == view:
                v.close()
                break

class ShowHideMinimap(VtAPI.Plugin.TextCommand):
    def __init__(self, api, view):
        self.api: VtAPI = api
        self.view = VtAPI.View = view
        super().__init__(api, view)
    def run(self):
        if self.view: self.view.setMmapHidden(not self.view.isMmapHidden())

def mMapActionUpdate(old: VtAPI.View, new: VtAPI.View):
    if new.isMmapHidden():
        pass

class InitFileTagsCommand(VtAPI.Plugin.TextCommand):
    def run(self, view=None):
        if view: self.view = view
        if self.view.getFile():
            tags = self.view.getTags(self.view.getFile())
            for tag in tags:
                self.view.addTag(self.view.getFile(), tag)

class AddTagCommand(VtAPI.Plugin.TextCommand):
    def run(self, tag=None):
        if not tag:
            text, dlg = self.api.Dialogs.inputDialog("Add tag")
            if text: tag = text
            else: return
        if self.view.getFile():
            self.view.addTag(self.view.getFile(), tag)
            self.view.window().signals.fileTagAdded.emit(self.view, tag)
        else:
            self.view.window().setLogMsg("Warning: Save file to add tag", vtApi.WARNING)
class RemoveTagCommand(VtAPI.Plugin.TextCommand):
    def run(self, tag=None, file=None, show=False):
        if not tag:
            text, dlg = self.api.Dialogs.inputDialog("Remove tag")
            if text: tag = text
            else: return
        if not file:
            if self.view.getFile():
                self.view.removeTag(self.view.getFile(), tag, show)
                self.view.window().signals.fileTagRemoved.emit(self.view, tag)
        else:
            self.view.removeTag(file, tag, show)
            self.api.activeWindow.signals.fileTagRemoved.emit(self.view, tag)              

class GetFilesForTagCommand(VtAPI.Plugin.TextCommand):
    def run(self, tag=None):
        if not tag:
            text, dlg = self.api.Dialogs.inputDialog("Get tag")
            if text: tag = text
            else: return
        self.tag = tag
        self.files = self.view.getTagFiles(tag)
        mLayout = self.initDialog()
        self.api.activeWindow.showDialog(mLayout, width=400, height=300)
    def initDialog(self):
        layout = QtWidgets.QVBoxLayout()
        
        self.listWidget = QtWidgets.QListWidget()
        layout.addWidget(self.listWidget)

        for file in self.files:
            self.add_file_item(file)
        return layout

    def add_file_item(self, filename: str):
        itemWidget = QtWidgets.QWidget()
        itemLayout = QtWidgets.QHBoxLayout(itemWidget)
        itemLayout.setContentsMargins(0, 0, 0, 0)

        itemLabel = QtWidgets.QLabel(filename)
        itemLayout.addWidget(itemLabel)

        openButton = QtWidgets.QPushButton()
        openButton.setFixedSize(20, 20)
        openButton.setIcon(QtGui.QIcon("icons/open.png"))
        openButton.setToolTip("Open File")
        openButton.clicked.connect(lambda: vtApi.activeWindow.openFiles([filename]))
        itemLayout.addWidget(openButton)

        deleteButton = QtWidgets.QPushButton()
        deleteButton.setFixedSize(20, 20)
        deleteButton.setIcon(QtGui.QIcon("icons/delete.png"))
        deleteButton.setToolTip("Remove Tag")
        deleteButton.clicked.connect(lambda: self.deleteTag(listItem, filename, self.tag))
        itemLayout.addWidget(deleteButton)

        listItem = QtWidgets.QListWidgetItem()
        listItem.setSizeHint(itemWidget.sizeHint())
        self.listWidget.addItem(listItem)
        self.listWidget.setItemWidget(listItem, itemWidget)
    
    def deleteTag(self, item, file, tag):
        for view in vtApi.activeWindow.views:
            if view.getFile() == file:
                self.listWidget.takeItem(self.listWidget.row(item))
                view.removeTag(tag=tag)

def parseThemes(path):
    files = []
    for file in vtApi.Path(path).dir():
        if vtApi.Path(path + '/' + file).isDir():
            files.extend(parseThemes(path + '/' + file))
        else:
            if str(file).endswith(".qss"):
                files.append(path + '/' + file)
    return files

def loadThemes():
    themes = []
    for theme in parseThemes(vtApi.themesDir):
        if vtApi.Path(vtApi.Path.joinPath(vtApi.themesDir, theme)).exists():
            themes.append({"caption": theme, "command": {"command": f"SetThemeCommand", "kwargs": {"theme": theme}}})
    vtApi.activeWindow.updateMenu("themes", themes)

def saveConsoleState():
    state = vtApi.Settings(vtApi.STATEFILE.get(vtApi.activeWindow.id))
    if state.has("state"):
        vtApi.addKey("state.logConsole.active", True, vtApi.CLOSINGSTATEFILE)

def restoreConsoleState():
    global consoleIsActive
    consoleIsActive = vtApi.findKey("state.logConsole.active", vtApi.STATEFILE.get(vtApi.activeWindow.id))
    if consoleIsActive:
        vtApi.activeWindow.runCommand({"command": "LogConsoleCommand", "kwargs": {"restoring": True, "state": consoleIsActive}})

def saveWState():
    tabWidgetTabsState = {}
    vtApi.addKey("settings.themeFile", vtApi.activeWindow.getTheme(), vtApi.CLOSINGSTATEFILE)
    vtApi.addKey("settings.locale", vtApi.activeWindow.getLocale(), vtApi.CLOSINGSTATEFILE)
    vtApi.addKey("state.splitter.data", vtApi.activeWindow.splitterData(), vtApi.CLOSINGSTATEFILE)
    vtApi.addKey("state.tabWidget.tabBar.movable", vtApi.activeWindow.isTabsMovable(), vtApi.CLOSINGSTATEFILE)
    vtApi.addKey("state.tabWidget.tabBar.closable", vtApi.activeWindow.isTabsClosable(), vtApi.CLOSINGSTATEFILE)
    index = vtApi.activeWindow.currentTreeIndex()
    if vtApi.activeWindow.model.isDir(index): vtApi.addKey("state.treeWidget.openedDir", vtApi.activeWindow.model.rootPath(), vtApi.CLOSINGSTATEFILE)
    if vtApi.activeWindow.activeView in vtApi.activeWindow.views: vtApi.addKey("state.tabWidget.activeTab", str(vtApi.activeWindow.activeView.tabIndex()), vtApi.CLOSINGSTATEFILE)
    stateFile = vtApi.Path.joinPath(vtApi.packagesDirs, '.ws')
    for view in vtApi.activeWindow.views:
        cursor = view.getTextCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        tabWidgetTabsState[str(view.tabIndex())] = {
            "name": view.getTitle(),
            "file": view.getFile(),
            "canSave": view.getCanSave(),
            "text": view.getText(),
            "isSaved": view.getSaved(),
            "selection": [start, end],
            # "modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mmapHidden": view.isMmapHidden()
        }
    vtApi.addKey("state.tabWidget.tabs", {str(idx): tabWidgetTabsState[str(idx)] for idx in range(len(tabWidgetTabsState))}, vtApi.CLOSINGSTATEFILE)
    if vtApi.Path(stateFile).isFile(): mode = 'wb'
    else: mode = 'ab'
    with open(stateFile, mode) as f: f.write(msgpack.packb(vtApi.CLOSINGSTATEFILE, use_bin_type=True))
    # self.settFile.close()

def restoreWState():
    vtApi.STATEFILE = {}
    stateFile = vtApi.Path.joinPath(vtApi.packagesDirs, '.ws')
    try:
        if vtApi.Path(stateFile).isFile():
            with open(stateFile, 'rb') as f:
                packed_data = f.read()
                vtApi.STATEFILE[vtApi.activeWindow.id] = msgpack.unpackb(packed_data, raw=False)
                for idx, tab in enumerate(vtApi.findKey("state.tabWidget.tabs", vtApi.STATEFILE.get(vtApi.activeWindow.id)) or []):
                    tab = vtApi.findKey(f"state.tabWidget.tabs.{str(idx)}", vtApi.STATEFILE.get(vtApi.activeWindow.id))
                    vtApi.activeWindow.newFile()
                    vtApi.activeWindow.activeView.setTitle(vtApi.findKey(f"state.tabWidget.tabs.{str(idx)}.name", vtApi.STATEFILE.get(vtApi.activeWindow.id)))
                    vtApi.activeWindow.activeView.setFile(vtApi.findKey(f"state.tabWidget.tabs.{str(idx)}.file", vtApi.STATEFILE.get(vtApi.activeWindow.id)))
                    vtApi.activeWindow.activeView.setText(vtApi.findKey(f"state.tabWidget.tabs.{str(idx)}.text", vtApi.STATEFILE.get(vtApi.activeWindow.id)))
                    vtApi.activeWindow.activeView.setCanSave(vtApi.findKey(f"state.tabWidget.tabs.{str(idx)}.canSave", vtApi.STATEFILE.get(vtApi.activeWindow.id)))
                    vtApi.activeWindow.setTitle(vtApi.Path(vtApi.activeWindow.activeView.getFile() or 'Untitled').normalize())
                    vtApi.activeWindow.activeView.setTextSelection(vtApi.Region(vtApi.findKey(f"state.tabWidget.tabs.{str(idx)}.selection", vtApi.STATEFILE.get(vtApi.activeWindow.id))[0], vtApi.findKey(f"state.tabWidget.tabs.{str(idx)}.selection", vtApi.STATEFILE.get(vtApi.activeWindow.id))[1]))
                    vtApi.activeWindow.activeView.setMmapHidden(vtApi.findKey(f"state.tabWidget.tabs.{str(idx)}.mmapHidden", vtApi.STATEFILE.get(vtApi.activeWindow.id)) or 0)
                    if vtApi.activeWindow.activeView.getFile(): vtApi.activeWindow.signals.fileOpened.emit(vtApi.activeWindow.activeView)
                    vtApi.activeWindow.activeView.setSaved(vtApi.findKey(f"state.tabWidget.tabs.{str(idx)}.isSaved", vtApi.STATEFILE.get(vtApi.activeWindow.id)))
                if vtApi.findKey("settings.themeFile", vtApi.STATEFILE.get(vtApi.activeWindow.id)): vtApi.activeWindow.setTheme(vtApi.findKey("settings.themeFile", vtApi.STATEFILE.get(vtApi.activeWindow.id)))
                if vtApi.findKey("settings.locale", vtApi.STATEFILE.get(vtApi.activeWindow.id)): vtApi.activeWindow.setLocale(vtApi.findKey("settings.locale", vtApi.STATEFILE.get(vtApi.activeWindow.id)))
                vtApi.activeWindow.setTreeWidgetDir(vtApi.findKey("state.treeWidget.openedDir", vtApi.STATEFILE.get(vtApi.activeWindow.id)) or "/")
                if vtApi.findKey("state.tabWidget.activeTab", vtApi.STATEFILE.get(vtApi.activeWindow.id)): vtApi.activeWindow.setTab(int(vtApi.findKey("state.tabWidget.activeTab", vtApi.STATEFILE.get(vtApi.activeWindow.id)))+1)
                if vtApi.findKey(f"state.splitter.data", vtApi.STATEFILE.get(vtApi.activeWindow.id)): vtApi.activeWindow.restoreSplitter(vtApi.findKey(f"state.splitter.data", vtApi.STATEFILE.get(vtApi.activeWindow.id)))
                vtApi.activeWindow.setTabsMovable(vtApi.findKey("state.tabWidget.tabBar.movable", vtApi.STATEFILE.get(vtApi.activeWindow.id)) or 1)
                vtApi.activeWindow.setTabsClosable(vtApi.findKey("state.tabWidget.tabBar.closable", vtApi.STATEFILE.get(vtApi.activeWindow.id)) or 1)

                newState = vtApi.STATEFILE.get(vtApi.activeWindow.id)
                vtApi.addKey("state.tabWidget.tabs", {}, newState)
                if vtApi.Path(stateFile).isFile(): mode = 'wb'
                else: mode = 'ab'
                with open(stateFile, mode) as f: f.write(msgpack.packb(newState, use_bin_type=True))
    except ValueError:
        vtApi.activeWindow.setLogMsg(f"\nFailed to restore window state. No file found at {stateFile}", vtApi.ERROR)