def initAPI(api):
    global VtAPI
    VtAPI = api
    os = VtAPI.importModule("os")
    shutil = VtAPI.importModule("shutil")
    zipfile = VtAPI.importModule("zipfile")
    uuid = VtAPI.importModule("uuid")
    json = VtAPI.importModule("json")
    req = VtAPI.importModule("urllib.request")
    err = VtAPI.importModule("urllib.error")
    QtWidgets = VtAPI.importModule("PyQt6.QtWidgets")
    QtGui = VtAPI.importModule("PyQt6.QtGui")
    QtCore = VtAPI.importModule("PyQt6.QtCore")

    global LogConsoleCommand, NewTabCommand, SelectAllCommand, CopyCommand, PasteCommand, CutCommand, UndoCommand, RedoCommand, SetThemeCommand, ShowPMCommand, CloseTabCommand, loadThemes, InitFileTagsCommand, AddTagCommand, RemoveTagCommand, ShowHideMinimap, GetFilesForTagCommand

    class LogConsoleCommand(VtAPI.Plugin.WindowCommand):
        def __init__(self, api, window):
            super().__init__(api, window)
            self.createWidget()
        def run(self, checked=None):
            if not self.api.activeWindow.isDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea):
                self.console = ConsoleWidget(self.api)
                self.console.textEdit.append(self.window.getLog())
                self.window.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self.console)
            else:
                self.console = self.window.isDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea)
                self.console.deleteLater()
        def createWidget(self):
            global ConsoleWidget
            class ConsoleWidget(VtAPI.Widgets.DockWidget):
                def __init__(self, api):
                    super().__init__()
                    self.api = api
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
                def sendCommand(self):
                    text = self.lineEdit.text()
                    if text:
                        if text.startswith("vtapi"):
                            if len(text.split(".")) == 2:
                                apiCommand = text.split(".")[-1] 
                                if hasattr(self.window.api, apiCommand):
                                    self.api.activeWindow.setLogMsg(str(getattr(self.window.api, apiCommand)()))
                            self.api.activeWindow.setLogMsg(str(self.window.api))
                            self.lineEdit.clear()
                        else:
                            self.api.activeWindow.runCommand({"command": self.lineEdit.text()})
                            self.lineEdit.clear()
                def closeEvent(self, e):
                    self.api.activeWindow.runCommand({"command": "LogConsoleCommand"})
                    e.ignore()

    class NewTabCommand(VtAPI.Plugin.WindowCommand):
        def run(self):
            self.window.newFile()

    class SelectAllCommand(VtAPI.Plugin.TextCommand):
        def run(self):
            self.view.selectAll()

    class CopyCommand(VtAPI.Plugin.TextCommand):
        def run(self):
            self.view.copy()

    class PasteCommand(VtAPI.Plugin.TextCommand):
        def run(self):
            cb = QtGui.QGuiApplication.clipboard()
            self.view.insert(cb.text())

    class CutCommand(VtAPI.Plugin.TextCommand):
        def run(self):
            self.view.cut()

    class UndoCommand(VtAPI.Plugin.TextCommand):
        def run(self):
            self.view.undo()

    class RedoCommand(VtAPI.Plugin.TextCommand):
        def run(self):
            self.view.redo()

    class SetThemeCommand(VtAPI.Plugin.WindowCommand):
        def run(self, theme):
            self.window.setTheme(theme)

    class ShowPMCommand(VtAPI.Plugin.WindowCommand):
        def run(self):
            mLayout = self.constructWindow(self.api.packagesDir)
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
            self.tempDir = os.getenv("TEMP")

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
                path = os.path.join(self.tempDir or os.path.dirname(__file__), tempdirName)
                os.makedirs(path)

                filePath = os.path.join(path, "package.zip")
                if site == "github":
                    req.urlretrieve(url + "/zipball/master", filePath)
                else:
                    req.urlretrieve(url, filePath)

                with zipfile.ZipFile(filePath, 'r') as f:
                    f.extractall(path)
                os.remove(filePath)

                extracted_dir = next(
                    os.path.join(path, d) for d in os.listdir(path)
                    if os.path.isdir(os.path.join(path, d))
                )
                if type == "plugin":
                    finalPackageDir = os.path.join(self.packagesDir, "Plugins", url.split("/")[-1])
                else:
                    finalPackageDir = os.path.join(self.packagesDir, "Themes", url.split("/")[-1])
                os.makedirs(self.packagesDir, exist_ok=True)

                shutil.move(extracted_dir, finalPackageDir)
                shutil.rmtree(path)

                self.checkReqs(finalPackageDir)
            except Exception as e:
                print(e)

        def tempname(self, n):
            return "vt-" + str(uuid.uuid4())[:n + 1] + "-install"

        def installModule(self, packages: str):
            import pip
            pip.main(["install", packages])

        def checkReqs(self, data):
            for url in data:
                if not os.path.isdir(os.path.join(self.packagesDir, url.split("/")[-1])):
                    self.install(url)

        def uninstall(self, name):
            dir_path = os.path.join(self.packagesDir, name)
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path)

        def search(self, type: str, name):
            dir_path = os.path.join(self.packagesDir, type.title(), name)
            return dir_path if os.path.isdir(dir_path) else ""

        def updateRepos(self):
            update_url = "http://127.0.0.1:8000/update"
            zip_path = os.path.join(self.api.cacheDir, "plugins.zip")
            req.urlretrieve(update_url, zip_path)

            with zipfile.ZipFile(zip_path, 'r') as f:
                f.extractall(self.api.cacheDir)
            os.remove(zip_path)

        def processPlugins(self):
            plugins_dir = os.path.join(self.api.cacheDir, "plugins")
            if not os.path.isdir(plugins_dir): os.makedirs(plugins_dir)
            for pl in os.listdir(plugins_dir):
                with open(os.path.join(plugins_dir, pl), "r") as f:
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
            themes_dir = os.path.join(self.api.cacheDir, "themes")
            if not os.path.isdir(themes_dir): os.makedirs(themes_dir)
            for th in os.listdir(themes_dir):
                with open(os.path.join(themes_dir, th), "r") as f:
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

    class ShowHideMinimap(VtAPI.Plugin.TextCommand):
        def run(self):
            if self.view: self.view.setMmapHidden(not self.view.isMmapHidden())

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
            openButton.clicked.connect(lambda: VtAPI.activeWindow.openFiles([filename]))
            itemLayout.addWidget(openButton)

            deleteButton = QtWidgets.QPushButton()
            deleteButton.setFixedSize(20, 20)
            deleteButton.setIcon(QtGui.QIcon("icons/delete.png"))
            deleteButton.setToolTip("Remove Tag")
            deleteButton.clicked.connect(lambda: VtAPI.activeWindow.runCommand({"command": "RemoveTagCommand", "kwargs": {"file": filename, "tag": self.tag}}))
            itemLayout.addWidget(deleteButton)

            listItem = QtWidgets.QListWidgetItem()
            listItem.setSizeHint(itemWidget.sizeHint())
            self.listWidget.addItem(listItem)
            self.listWidget.setItemWidget(listItem, itemWidget)
    def parseThemes(path):
        files = []
        for file in os.listdir(path):
            if os.path.isdir(path + '/' + file):
                files.extend(parseThemes(path + '/' + file))
            else:
                if str(file).endswith(".qss"):
                    files.append(path + '/' + file)
        return files

    def loadThemes():
        themes = []
        for theme in parseThemes(VtAPI.themesDir):
            if os.path.isfile(os.path.join(VtAPI.themesDir, theme)):
                themes.append({"caption": theme, "command": {"command": f"SetThemeCommand", "kwargs": {"theme": theme}}})
        VtAPI.activeWindow.updateMenu("themes", themes)

    VtAPI.activeWindow.registerCommandClass({"command": SetThemeCommand})
    VtAPI.activeWindow.registerCommandClass({"command": ShowHideMinimap})
    VtAPI.activeWindow.registerCommandClass({"command": InitFileTagsCommand})
    VtAPI.activeWindow.registerCommandClass({"command": GetFilesForTagCommand})
    VtAPI.activeWindow.registerCommandClass({"command": AddTagCommand, "shortcut": "ctrl+f"})
    VtAPI.activeWindow.registerCommandClass({"command": RemoveTagCommand})
    VtAPI.activeWindow.signals.fileOpened.connect(lambda: VtAPI.activeWindow.runCommand({"command": "InitFileTagsCommand", "kwargs": {"view": VtAPI.activeWindow.activeView}}))
    VtAPI.activeWindow.signals.windowStarted.connect(loadThemes)