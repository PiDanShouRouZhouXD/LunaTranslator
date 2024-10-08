from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from qtsymbols import *
import os, functools, uuid, threading, hashlib, shutil, time
from datetime import datetime, timedelta
from traceback import print_exc
import windows, gobject, winsharedutils, qtawesome
from myutils.config import (
    savehook_new_list,
    savehook_new_data,
    savegametaged,
    uid2gamepath,
    _TR,
    postprocessconfig,
    extradatas,
    globalconfig,
    static_data,
)
from myutils.localetools import getgamecamptools, localeswitchedrun, maycreatesettings
from myutils.hwnd import getExeIcon
from myutils.wrapper import (
    Singleton_close,
    Singleton,
    threader,
    tryprint,
    Singleton_close,
)
from myutils.utils import (
    find_or_create_uid,
    str2rgba,
    duplicateconfig,
    get_time_stamp,
    gamdidchangedtask,
    checkpostlangmatch,
    loadpostsettingwindowmethod_private,
    titlechangedtask,
    selectdebugfile,
    targetmod,
    loopbackrecorder,
)
from myutils.audioplayer import playonce
from gui.codeacceptdialog import codeacceptdialog
from gui.inputdialog import (
    noundictconfigdialog1,
    yuyinzhidingsetting,
    postconfigdialog2x,
    autoinitdialog,
    autoinitdialog_items,
    postconfigdialog,
)
from gui.specialwidget import (
    ScrollFlow,
    chartwidget,
    lazyscrollflow,
    stackedlist,
    shrinkableitem,
)
from gui.usefulwidget import (
    yuitsu_switch,
    pixmapviewer,
    FocusCombo,
    TableViewW,
    saveposwindow,
    getsimplepatheditor,
    getboxlayout,
    getlineedit,
    statusbutton,
    MySwitch,
    auto_select_webview,
    Prompt_dialog,
    clearlayout,
    getsimplecombobox,
    D_getsimpleswitch,
    getspinbox,
    getIconButton,
    D_getIconButton,
    getcolorbutton,
    makesubtab_lazy,
    tabadd_lazy,
    getsimpleswitch,
    threebuttons,
    FQLineEdit,
    getspinbox,
    selectcolor,
    listediter,
    listediterline,
)
from gui.dynalang import (
    LFormLayout,
    LPushButton,
    LStandardItemModel,
    LDialog,
    LAction,
    LLabel,
)


class ItemWidget(QWidget):
    focuschanged = pyqtSignal(bool, str)
    doubleclicked = pyqtSignal(str)
    globallashfocus = None

    @classmethod
    def clearfocus(cls):
        try:  # 可能已被删除
            if ItemWidget.globallashfocus:
                ItemWidget.globallashfocus.focusOut()
        except:
            pass
        ItemWidget.globallashfocus = None

    def click(self):
        try:
            self.bottommask.setStyleSheet(
                f'background-color: {str2rgba(globalconfig["dialog_savegame_layout"]["onselectcolor1"],globalconfig["dialog_savegame_layout"]["transparentselect"])};'
            )

            if self != ItemWidget.globallashfocus:
                ItemWidget.clearfocus()
            ItemWidget.globallashfocus = self
            self.focuschanged.emit(True, self.gameuid)
        except:
            print_exc()

    def mousePressEvent(self, ev) -> None:
        self.click()

    def focusOut(self):
        self.bottommask.setStyleSheet("background-color: rgba(255,255,255, 0);")
        self.focuschanged.emit(False, self.gameuid)

    def mouseDoubleClickEvent(self, e):
        self.doubleclicked.emit(self.gameuid)

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.bottommask.resize(a0.size())
        self.maskshowfileexists.resize(a0.size())

    def __init__(self, gameuid, pixmap, file) -> None:
        super().__init__()
        self.itemw = globalconfig["dialog_savegame_layout"]["itemw"]
        self.itemh = globalconfig["dialog_savegame_layout"]["itemh"]
        # self.imgw = globalconfig["dialog_savegame_layout"]["imgw"]
        # self.imgh = globalconfig["dialog_savegame_layout"]["imgh"]
        # margin = (
        #     self.itemw - self.imgw
        # ) // 2  # globalconfig['dialog_savegame_layout']['margin']
        margin = globalconfig["dialog_savegame_layout"]["margin"]
        if globalconfig["showgametitle"]:
            textH = globalconfig["dialog_savegame_layout"]["textH"]
        else:
            textH = 0
        self.imgw = self.itemw - 2 * margin
        self.imgh = self.itemh - textH - 2 * margin
        #
        self.setFixedSize(QSize(self.itemw, self.itemh))
        # self.setFocusPolicy(Qt.StrongFocus)
        self.maskshowfileexists = QLabel(self)
        self.bottommask = QLabel(self)
        self.bottommask.setStyleSheet("background-color: rgba(255,255,255, 0);")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self._img = IMGWidget(self.imgw, self.imgh, pixmap)
        _w = QWidget()
        _w.setStyleSheet("background-color: rgba(255,255,255, 0);")
        wrap = QVBoxLayout()
        _w.setLayout(wrap)
        _w.setFixedHeight(self.imgh + 2 * margin)
        wrap.setContentsMargins(margin, margin, margin, margin)
        wrap.addWidget(self._img)
        layout.addWidget(_w)
        layout.setSpacing(0)
        self._lb = QLabel()
        if globalconfig["showgametitle"]:
            self._lb.setText(file)
        self._lb.setWordWrap(True)
        self._lb.setStyleSheet("background-color: rgba(255,255,255, 0);")
        self._lb.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._lb)
        self.setLayout(layout)
        self.gameuid = gameuid
        c = globalconfig["dialog_savegame_layout"][
            ("onfilenoexistscolor1", "backcolor1")[
                os.path.exists(uid2gamepath[gameuid])
            ]
        ]
        c = str2rgba(
            c,
            globalconfig["dialog_savegame_layout"][
                ("transparentnotexits", "transparent")[
                    os.path.exists(uid2gamepath[gameuid])
                ]
            ],
        )
        self.maskshowfileexists.setStyleSheet(f"background-color:{c};")


class IMGWidget(QLabel):

    def adaptsize(self, size: QSize):

        if globalconfig["imagewrapmode"] == 0:
            h, w = size.height(), size.width()
            r = float(w) / h
            max_r = float(self.width()) / self.height()
            if r < max_r:
                new_w = self.width()
                new_h = int(new_w / r)
            else:
                new_h = self.height()
                new_w = int(new_h * r)
            return QSize(new_w, new_h)
        elif globalconfig["imagewrapmode"] == 1:
            h, w = size.height(), size.width()
            r = float(w) / h
            max_r = float(self.width()) / self.height()
            if r > max_r:
                new_w = self.width()
                new_h = int(new_w / r)
            else:
                new_h = self.height()
                new_w = int(new_h * r)
            return QSize(new_w, new_h)
        elif globalconfig["imagewrapmode"] == 2:
            return self.size()
        elif globalconfig["imagewrapmode"] == 3:
            return size

    def setimg(self, pixmap):
        if type(pixmap) != QPixmap:
            pixmap = pixmap()

        rate = self.devicePixelRatioF()
        newpixmap = QPixmap(self.size() * rate)
        newpixmap.setDevicePixelRatio(rate)
        newpixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(newpixmap)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawPixmap(self.getrect(pixmap.size()), pixmap)
        painter.end()

        self.setPixmap(newpixmap)

    def getrect(self, size):
        size = self.adaptsize(size)
        rect = QRect()
        rect.setX(int((self.width() - size.width()) / 2))
        rect.setY(int((self.height() - size.height()) / 2))
        rect.setSize(size)
        return rect

    def __init__(self, w, h, pixmap) -> None:
        super().__init__()
        self.setFixedSize(QSize(w, h))
        self.setScaledContents(True)
        self.setimg(pixmap)


class ClickableLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setClickable(True)

    def setClickable(self, clickable):
        self._clickable = clickable

    def mousePressEvent(self, event):
        if self._clickable and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    clicked = pyqtSignal()


class tagitem(QWidget):
    # website
    TYPE_GLOABL_LIKE = 3
    TYPE_GAME_LIKE = 1
    # search game
    TYPE_RAND = 0
    TYPE_DEVELOPER = 1
    TYPE_TAG = 2
    TYPE_USERTAG = 3
    TYPE_EXISTS = 4
    removesignal = pyqtSignal(tuple)
    labelclicked = pyqtSignal(tuple)

    def remove(self):
        self.hide()
        _lay = self.layout()
        _ws = []
        for i in range(_lay.count()):
            witem = _lay.itemAt(i)
            _ws.append(witem.widget())
        for w in _ws:
            _lay.removeWidget(w)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._type == tagitem.TYPE_RAND:
            border_color = Qt.GlobalColor.black
        elif self._type == tagitem.TYPE_DEVELOPER:
            border_color = Qt.GlobalColor.red
        elif self._type == tagitem.TYPE_TAG:
            border_color = Qt.GlobalColor.green
        elif self._type == tagitem.TYPE_USERTAG:
            border_color = Qt.GlobalColor.blue
        elif self._type == tagitem.TYPE_EXISTS:
            border_color = Qt.GlobalColor.yellow
        border_width = 1
        pen = QPen(border_color)
        pen.setWidth(border_width)
        painter.setPen(pen)
        painter.drawRect(self.rect())

    def __init__(self, tag, removeable=True, _type=TYPE_RAND, refdata=None) -> None:
        super().__init__()
        tagLayout = QHBoxLayout()
        tagLayout.setContentsMargins(0, 0, 0, 0)
        tagLayout.setSpacing(0)
        self._type = _type
        key = (tag, _type, refdata)
        self.setLayout(tagLayout)
        lb = ClickableLabel()
        lb.setStyleSheet("background: transparent;")
        lb.setText(tag)
        lb.clicked.connect(functools.partial(self.labelclicked.emit, key))
        tagLayout.addWidget(lb)
        if removeable:
            button = getIconButton(
                functools.partial(self.removesignal.emit, key), icon="fa.times"
            )
            tagLayout.addWidget(button)


class TagWidget(QWidget):
    tagschanged = pyqtSignal(tuple)  # ((tag,type,refdata),)
    linepressedenter = pyqtSignal(str)
    tagclicked = pyqtSignal(tuple)  # tag,type,refdata

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

        self.lineEdit = FocusCombo()
        self.lineEdit.setLineEdit(FQLineEdit())

        self.lineEdit.lineEdit().returnPressed.connect(
            lambda: self.linepressedenter.emit(self.lineEdit.currentText())
        )

        self.lineEdit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )

        layout.addWidget(self.lineEdit)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.tag2widget = {}

    def addTags(self, tags, signal=True):
        for key in tags:
            self.__addTag(key)
        self.__calltagschanged(signal)

    @tryprint
    def __addTag(self, key):
        tag, _type, refdata = key
        if not tag:
            return
        if key in self.tag2widget:
            return
        qw = tagitem(tag, _type=_type, refdata=refdata)
        qw.removesignal.connect(self.removeTag)
        qw.labelclicked.connect(self.tagclicked.emit)
        layout = self.layout()
        layout.insertWidget(layout.count() - 1, qw)
        self.tag2widget[key] = qw
        self.lineEdit.setFocus()

    def addTag(self, tag, _type, refdata=None, signal=True):
        self.__addTag((tag, _type, refdata))
        self.__calltagschanged(signal)

    @tryprint
    def __removeTag(self, key):
        _w = self.tag2widget[key]
        _w.remove()

        self.layout().removeWidget(_w)
        self.tag2widget.pop(key)

    def removeTag(self, key, signal=True):
        self.__removeTag(key)
        self.__calltagschanged(signal)

    def __calltagschanged(self, signal):
        if signal:
            self.tagschanged.emit(tuple(self.tag2widget.keys()))

    def clearTag(self, signal=True):
        for key in self.tag2widget.copy():
            self.__removeTag(key)
        self.__calltagschanged(signal)


@Singleton
class browserdialog(saveposwindow):
    seturlsignal = pyqtSignal(str)

    def startupsettitle(self, gameuid):

        if gameuid:
            title = savehook_new_data[gameuid]["title"]
        else:
            title = "LunaTranslator"
        self.setWindowTitle(title)

    def loadalllinks(self, gameuid):
        items = []
        if gameuid:
            self.setWindowTitle(savehook_new_data[gameuid]["title"])

        for link in globalconfig["relationlinks"]:
            items.append((link[0], tagitem.TYPE_GLOABL_LIKE, link[1]))
        if gameuid:
            for link in savehook_new_data[self.gameuid]["relationlinks"]:
                items.append((link[0], tagitem.TYPE_GAME_LIKE, link[1]))
        if len(items) == 0:
            items.append(
                (
                    "Luna",
                    tagitem.TYPE_GLOABL_LIKE,
                    static_data["main_server"][gobject.serverindex],
                )
            )
        self.tagswidget.clearTag(False)
        self.tagswidget.addTags(items)

    def startupnavi(self, gameuid):
        for idx in range(2, 100):
            if idx == 2:
                if gameuid:
                    if len(savehook_new_data[gameuid]["relationlinks"]):
                        navitarget = savehook_new_data[gameuid]["relationlinks"][-1][1]
                        break
            elif idx == 3:
                if len(globalconfig["relationlinks"]):
                    navitarget = globalconfig["relationlinks"][-1][1]
                    break
            else:
                navitarget = None
                break
        if navitarget:
            self.browser.navigate(navitarget)
            self.urlchanged(navitarget)

    def urlchanged(self, url):
        self.tagswidget.lineEdit.setCurrentText(url)
        self.current = url

    def likelink(self):
        _dia = Prompt_dialog(
            self,
            "收藏",
            "",
            [
                ["名称", ""],
                ["网址", self.current],
            ],
        )

        if _dia.exec():

            text = []
            for _t in _dia.text:
                text.append(_t.text())
            if self.gameuid:
                savehook_new_data[self.gameuid]["relationlinks"].append(text)
                self.tagswidget.addTag(text[0], tagitem.TYPE_GAME_LIKE, text[1])
            else:
                globalconfig["relationlinks"].append(text)
                self.tagswidget.addTag(text[0], tagitem.TYPE_GLOABL_LIKE, text[1])

    def tagschanged(self, tags):
        __ = []
        __2 = []
        for _name, _type, _url in tags:
            if _type == tagitem.TYPE_GLOABL_LIKE:
                __.append([_name, _url])
            elif _type == tagitem.TYPE_GAME_LIKE:
                __2.append([_name, _url])
        globalconfig["relationlinks"] = __
        if self.gameuid:
            savehook_new_data[self.gameuid]["relationlinks"] = __2

    def reinit(self, gameuid=None):

        self.gameuid = gameuid
        self.loadalllinks(gameuid)
        self.startupnavi(gameuid)
        self.startupsettitle(gameuid)

    def __init__(self, parent, gameuid=None) -> None:
        super().__init__(parent, poslist=globalconfig["browserwidget"])
        if gameuid:
            self.setWindowIcon(getExeIcon(uid2gamepath[gameuid], cache=True))
        self.browser = auto_select_webview(self)

        self.tagswidget = TagWidget(self)
        self.tagswidget.tagschanged.connect(self.tagschanged)

        self.tagswidget.tagclicked.connect(self.urlclicked)
        self.tagswidget.linepressedenter.connect(self.browser.navigate)
        self.browser.on_load.connect(self.urlchanged)

        hlay = QHBoxLayout()
        hlay.addWidget(self.tagswidget)

        hlay.addWidget(getIconButton(self.likelink, icon="fa.heart"))
        hlay.addWidget(
            getIconButton(
                lambda: self.urlclicked((None, None, self.current)), icon="fa.repeat"
            )
        )
        _topw = QWidget()
        _topw.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        _topw.setLayout(hlay)
        layout = QVBoxLayout()
        layout.setContentsMargins(*(0 for i in range(4)))
        hlay.setContentsMargins(*(0 for i in range(4)))
        layout.addWidget(_topw)
        layout.addWidget(self.browser)
        layout.setSpacing(0)
        __w = QWidget()
        __w.setLayout(layout)
        self.setCentralWidget(__w)

        self.reinit(gameuid)
        self.show()

    def urlclicked(self, _):
        tag, _, url = _
        if url[:4].lower() != "http":
            url = os.path.abspath(url)
        self.browser.navigate(url)

    def showmenu(self, p):
        tab_index = self.nettab.tabBar().tabAt(p)
        if (self.hasvndb and tab_index == 0) or tab_index == self.nettab.count() - 1:
            return
        menu = QMenu(self)
        shanchu = LAction(("删除"))
        menu.addAction(shanchu)
        action = menu.exec(self.mapToGlobal(p))
        if action == shanchu:
            self.nettab.setCurrentIndex(0)
            self.nettab.removeTab(tab_index)
            savehook_new_data[self.gameuid]["relationlinks"].pop(
                tab_index - self.hasvndb
            )


_global_dialog_savedgame_new = None
_global_dialog_setting_game = None


def calculate_centered_rect(original_rect: QRect, size: QSize) -> QRect:
    original_center = original_rect.center()
    new_left = original_center.x() - size.width() // 2
    new_top = original_center.y() - size.height() // 2
    new_rect = QRect(new_left, new_top, size.width(), size.height())
    return new_rect


def maybehavebutton(self, gameuid, post):
    if post == "_11":
        savehook_new_data[gameuid]["save_text_process_info"]["mypost"] = str(
            uuid.uuid4()
        ).replace("-", "_")
        return getIconButton(
            callback=functools.partial(
                selectdebugfile,
                savehook_new_data[gameuid]["save_text_process_info"]["mypost"],
                ismypost=True,
            ),
            icon="fa.gear",
        )
    else:
        if post not in postprocessconfig:
            return
        if post == "_remove_chaos":
            return getIconButton(
                icon="fa.gear", callback=lambda: codeacceptdialog(self)
            )
        elif "args" in postprocessconfig[post]:
            if post == "stringreplace":
                callback = functools.partial(
                    postconfigdialog2x,
                    self,
                    savehook_new_data[gameuid]["save_text_process_info"][
                        "postprocessconfig"
                    ][post]["args"]["internal"],
                    savehook_new_data[gameuid]["save_text_process_info"][
                        "postprocessconfig"
                    ][post]["name"],
                    ["正则", "转义", "原文内容", "替换为"],
                )
            elif isinstance(list(postprocessconfig[post]["args"].values())[0], dict):
                callback = functools.partial(
                    postconfigdialog,
                    self,
                    savehook_new_data[gameuid]["save_text_process_info"][
                        "postprocessconfig"
                    ][post]["args"]["替换内容"],
                    postprocessconfig[post]["name"],
                    ["原文内容", "替换为"],
                )
            else:
                items = autoinitdialog_items(
                    savehook_new_data[gameuid]["save_text_process_info"][
                        "postprocessconfig"
                    ][post]
                )
                callback = functools.partial(
                    autoinitdialog,
                    self,
                    postprocessconfig[post]["name"],
                    600,
                    items,
                )
            return getIconButton(callback=callback, icon="fa.gear")
        else:
            return None


class dialog_setting_game_internal(QWidget):
    def selectexe(self):
        originpath = uid2gamepath[self.gameuid]
        f = QFileDialog.getOpenFileName(directory=originpath)
        res = f[0]
        if res == "":
            return
        # 修改路径允许路径重复
        # 添加路径实际上也允许重复，只不过会去重。
        res = os.path.normpath(res)
        uid2gamepath[self.gameuid] = res
        gobject.baseobject.resetgameinternal(originpath, res)
        _icon = getExeIcon(res, cache=True)

        self.setWindowIcon(_icon)
        self.editpath.setText(res)

    def __init__(self, parent, gameuid) -> None:
        super().__init__(parent)
        vbox = QVBoxLayout(self)
        formLayout = LFormLayout()
        self.setLayout(vbox)
        self.gameuid = gameuid
        self.editpath = QLineEdit(uid2gamepath[gameuid])
        self.editpath.setReadOnly(True)
        formLayout.addRow(
            "路径",
            getboxlayout(
                [
                    self.editpath,
                    getIconButton(functools.partial(self.selectexe), icon="fa.gear"),
                    getIconButton(
                        lambda: browserdialog(
                            gobject.baseobject.commonstylebase, gameuid
                        ),
                        icon="fa.book",
                    ),
                ]
            ),
        )
        titleedit = QLineEdit(savehook_new_data[gameuid]["title"])

        def _titlechange():
            x = titleedit.text()
            titlechangedtask(gameuid, x)
            self.setWindowTitle(x)

        titleedit.textEdited.connect(
            functools.partial(savehook_new_data[gameuid].__setitem__, "title")
        )
        titleedit.returnPressed.connect(_titlechange)

        formLayout.addRow(
            "标题",
            getboxlayout(
                [
                    titleedit,
                    getIconButton(_titlechange, icon="fa.search"),
                ]
            ),
        )

        functs = [
            ("游戏设置", functools.partial(self.___tabf3, self.makegamesettings)),
            ("游戏数据", functools.partial(self.___tabf3, self.makegamedata)),
        ]
        methodtab, do = makesubtab_lazy(
            [_[0] for _ in functs],
            [functools.partial(self.doaddtab, _[1], gameuid) for _ in functs],
            delay=True,
        )
        vbox.addLayout(formLayout)
        vbox.addWidget(methodtab)
        do()

    def ___tabf(self, function, gameuid):
        _w = QWidget()
        formLayout = LFormLayout()
        _w.setLayout(formLayout)
        do = functools.partial(function, formLayout, gameuid)
        return _w, do

    def ___tabf2(self, function, gameuid):
        _w = QWidget()
        formLayout = QVBoxLayout()
        _w.setLayout(formLayout)
        do = functools.partial(function, formLayout, gameuid)
        return _w, do

    def ___tabf3(self, function, gameuid):
        _w = QWidget()
        formLayout = QVBoxLayout()
        formLayout.setContentsMargins(0, 0, 0, 0)
        _w.setLayout(formLayout)
        do = functools.partial(function, formLayout, gameuid)
        return _w, do

    def makegamedata(self, vbox: QVBoxLayout, gameuid):

        functs = [
            ("元数据", functools.partial(self.___tabf, self.metadataorigin)),
            ("统计", functools.partial(self.___tabf2, self.getstatistic)),
            ("标签", functools.partial(self.___tabf2, self.getlabelsetting)),
        ]
        methodtab, do = makesubtab_lazy(
            [_[0] for _ in functs],
            [functools.partial(self.doaddtab, _[1], gameuid) for _ in functs],
            delay=True,
        )
        vbox.addWidget(methodtab)
        do()

    def makegamesettings(self, vbox: QVBoxLayout, gameuid):

        functs = [
            ("启动", functools.partial(self.___tabf, self.starttab)),
            ("HOOK", functools.partial(self.___tabf, self.gethooktab)),
            ("语言", functools.partial(self.___tabf, self.getlangtab)),
            ("文本处理", functools.partial(self.___tabf, self.gettextproc)),
            ("翻译优化", functools.partial(self.___tabf, self.gettransoptimi)),
            ("语音", functools.partial(self.___tabf, self.getttssetting)),
            ("预翻译", functools.partial(self.___tabf, self.getpretranstab)),
        ]
        methodtab, do = makesubtab_lazy(
            [_[0] for _ in functs],
            [functools.partial(self.doaddtab, _[1], gameuid) for _ in functs],
            delay=True,
        )

        self.methodtab = methodtab
        vbox.addWidget(methodtab)
        do()

    def openrefmainpage(self, key, idname, gameuid):
        try:
            gobject.baseobject.openlink(
                targetmod[key].refmainpage(savehook_new_data[gameuid][idname])
            )
        except:
            print_exc()

    def metadataorigin(self, formLayout: LFormLayout, gameuid):
        formLayout.addRow(
            "首选的",
            getsimplecombobox(
                list(targetmod.keys()),
                globalconfig,
                "primitivtemetaorigin",
                internal=list(targetmod.keys()),
                static=True,
            ),
        )
        formLayout.addRow(None, QLabel())
        for key in targetmod:
            try:
                idname = targetmod[key].idname

                vndbid = QLineEdit()
                vndbid.setText(str(savehook_new_data[gameuid].get(idname, "")))
                vndbid.setSizePolicy(
                    QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
                )

                vndbid.textEdited.connect(
                    functools.partial(savehook_new_data[gameuid].__setitem__, idname)
                )
                vndbid.returnPressed.connect(
                    functools.partial(gamdidchangedtask, key, idname, gameuid)
                )
                _vbox_internal = [
                    getsimpleswitch(globalconfig["metadata"][key], "auto"),
                    vndbid,
                    getIconButton(
                        functools.partial(self.openrefmainpage, key, idname, gameuid),
                        icon="fa.chrome",
                    ),
                    getIconButton(
                        functools.partial(gamdidchangedtask, key, idname, gameuid),
                        icon="fa.search",
                    ),
                ]
            except:
                print_exc()
                continue
            try:
                __settting = targetmod[key].querysettingwindow
                _vbox_internal.insert(
                    2,
                    getIconButton(
                        functools.partial(__settting, self, gameuid), icon="fa.gear"
                    ),
                )
            except:
                pass
            formLayout.addRow(
                key,
                getboxlayout(_vbox_internal),
            )

    def doaddtab(self, wfunct, exe, layout):
        w, do = wfunct(exe)
        layout.addWidget(w)
        do()

    def starttab(self, formLayout: LFormLayout, gameuid):
        box = QGroupBox()
        settinglayout = LFormLayout()
        box.setLayout(settinglayout)

        def __(box, layout, config, uid):
            clearlayout(layout)
            maycreatesettings(layout, config, uid)
            if layout.count() == 0:
                box.hide()
            else:
                box.show()

        __launch_method = getsimplecombobox(
            [_.name for _ in getgamecamptools(uid2gamepath[gameuid])],
            savehook_new_data[gameuid],
            "launch_method",
            internal=[_.id for _ in getgamecamptools(uid2gamepath[gameuid])],
            callback=functools.partial(
                __, box, settinglayout, savehook_new_data[gameuid]
            ),
        )
        formLayout.addRow("启动方式", __launch_method)
        formLayout.addRow(box)

        formLayout.addRow(
            "自动切换到模式",
            getsimplecombobox(
                ["不切换", "HOOK", "剪贴板", "OCR"],
                savehook_new_data[gameuid],
                "onloadautochangemode2",
            ),
        )

        __launch_method.currentIndexChanged.emit(__launch_method.currentIndex())

    def getstatistic(self, formLayout: QVBoxLayout, gameuid):
        chart = chartwidget()
        chart.xtext = lambda x: (
            "0" if x == 0 else str(datetime.fromtimestamp(x)).split(" ")[0]
        )
        chart.ytext = lambda y: self.formattime(y, False)

        self.chart = chart
        self._timelabel = QLabel()
        self._wordlabel = QLabel()
        self._wordlabel.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        self._timelabel.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        formLayout.addLayout(getboxlayout([LLabel(("文字计数")), self._wordlabel]))
        formLayout.addLayout(getboxlayout([LLabel(("游戏时间")), self._timelabel]))

        formLayout.addWidget(chart)
        t = QTimer(self)
        t.setInterval(1000)
        t.timeout.connect(self.refresh)
        t.timeout.emit()
        t.start()

    def split_range_into_days(self, times):
        everyday = {}
        for start, end in times:
            if start == 0:
                everyday[0] = end
                continue

            start_date = datetime.fromtimestamp(start)
            end_date = datetime.fromtimestamp(end)

            current_date = start_date
            while current_date <= end_date:
                end_of_day = current_date.replace(
                    hour=23, minute=59, second=59, microsecond=0
                )
                end_of_day = end_of_day.timestamp() + 1

                if end_of_day >= end_date.timestamp():
                    useend = end_date.timestamp()
                else:
                    useend = end_of_day
                duration = useend - current_date.timestamp()
                today = end_of_day - 1
                if today not in everyday:
                    everyday[today] = 0
                everyday[today] += duration
                current_date += timedelta(days=1)
                current_date = current_date.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
        lists = []
        for k in sorted(everyday.keys()):
            lists.append((k, everyday[k]))
        return lists

    def refresh(self):
        __ = gobject.baseobject.querytraceplaytime_v4(self.gameuid)
        _cnt = sum([_[1] - _[0] for _ in __])
        savehook_new_data[self.gameuid]["statistic_playtime"] = _cnt
        self._timelabel.setText(self.formattime(_cnt))
        self._wordlabel.setText(
            str(savehook_new_data[self.gameuid]["statistic_wordcount"])
        )
        self.chart.setdata(self.split_range_into_days(__))

    def formattime(self, t, usingnotstart=True):
        t = int(t)
        s = t % 60
        t = t // 60
        m = t % 60
        t = t // 60
        h = t
        string = ""
        if h:
            string += str(h) + _TR("时")
        if m:
            string += str(m) + _TR("分")
        if s:
            string += str(s) + _TR("秒")
        if string == "":
            if usingnotstart:
                string = _TR("未开始")
            else:
                string = "0"
        return string

    def getlabelsetting(self, formLayout: QVBoxLayout, gameuid):
        self.labelflow = ScrollFlow()

        def newitem(text, refkey, first=False, _type=tagitem.TYPE_RAND):
            qw = tagitem(text, True, _type)

            def __(_qw, refkey, _):
                t, _type, _ = _
                try:
                    _qw.remove()
                    savehook_new_data[gameuid][refkey].remove(t)
                    self.labelflow.removewidget(_qw)
                except:
                    print_exc()

            qw.removesignal.connect(functools.partial(__, qw, refkey))

            def safeaddtags(_):
                try:
                    _global_dialog_savedgame_new.tagswidget.addTag(*_)
                except:
                    pass

            qw.labelclicked.connect(safeaddtags)
            if first:
                self.labelflow.insertwidget(0, qw)
            else:
                self.labelflow.addwidget(qw)

        for tag in savehook_new_data[gameuid]["usertags"]:
            newitem(tag, "usertags", _type=tagitem.TYPE_USERTAG)
        for tag in savehook_new_data[gameuid]["developers"]:
            newitem(tag, "developers", _type=tagitem.TYPE_DEVELOPER)
        for tag in savehook_new_data[gameuid]["webtags"]:
            newitem(tag, "webtags", _type=tagitem.TYPE_TAG)
        formLayout.addWidget(self.labelflow)
        _dict = {"new": 0}

        formLayout.addWidget(self.labelflow)
        button = LPushButton("添加")

        combo = getsimplecombobox(globalconfig["labelset"], _dict, "new", static=True)
        combo.setEditable(True)
        combo.clearEditText()

        def _add(_):

            tag = combo.currentText()
            # tag = globalconfig["labelset"][_dict["new"]]
            if tag and tag not in savehook_new_data[gameuid]["usertags"]:
                savehook_new_data[gameuid]["usertags"].insert(0, tag)
                newitem(tag, True, True, _type=tagitem.TYPE_USERTAG)
            combo.clearEditText()

        button.clicked.connect(_add)

        formLayout.addLayout(
            getboxlayout(
                [
                    combo,
                    button,
                ]
            )
        )

    def createfollowdefault(
        self, dic: dict, key: str, formLayout: LFormLayout, callback=None
    ) -> LFormLayout:

        __extraw = QWidget()

        def __function(__extraw: QWidget, callback, _):
            __extraw.setEnabled(not _)
            if callback:
                try:
                    callback()
                except:
                    print_exc()

        formLayout.addRow(
            "跟随默认",
            getsimpleswitch(
                dic,
                key,
                callback=functools.partial(__function, __extraw, callback),
            ),
        )
        __extraw.setEnabled(not dic[key])
        formLayout.addRow(__extraw)
        formLayout2 = LFormLayout()
        formLayout2.setContentsMargins(0, 0, 0, 0)
        __extraw.setLayout(formLayout2)
        return formLayout2

    def getttssetting(self, formLayout: LFormLayout, gameuid):
        formLayout2 = self.createfollowdefault(
            savehook_new_data[gameuid], "tts_follow_default", formLayout
        )
        if "tts_repair_use_at_translate" not in savehook_new_data[gameuid]:
            savehook_new_data[gameuid]["tts_repair_use_at_translate"] = globalconfig[
                "ttscommon"
            ]["tts_repair"]
        formLayout2.addRow(
            "语音指定",
            getboxlayout(
                [
                    getsimpleswitch(savehook_new_data[gameuid], "tts_skip"),
                    getIconButton(
                        callback=lambda: yuyinzhidingsetting(
                            self, savehook_new_data[gameuid]["tts_skip_regex"]
                        ),
                        icon="fa.gear",
                    ),
                    QLabel(),
                ],
                margin0=True,
                makewidget=True,
            ),
        )
        formLayout2.addRow(
            "语音修正",
            getboxlayout(
                [
                    getsimpleswitch(savehook_new_data[gameuid], "tts_repair"),
                    getIconButton(
                        callback=lambda: noundictconfigdialog1(
                            self,
                            savehook_new_data[gameuid]["tts_repair_regex"],
                            "语音修正",
                            ["正则", "转义", "原文", "替换"],
                        ),
                        icon="fa.gear",
                    ),
                    QLabel(),
                    getsimpleswitch(
                        savehook_new_data[gameuid], "tts_repair_use_at_translate"
                    ),
                    LLabel("作用于翻译"),
                ],
                margin0=True,
                makewidget=True,
            ),
        )

    def getpretranstab(self, formLayout: LFormLayout, gameuid):

        def selectimg(gameuid, key, res):
            savehook_new_data[gameuid][key] = res

        for showname, key, filt in [
            ("json翻译文件", "gamejsonfile", "*.json"),
        ]:
            if isinstance(savehook_new_data[gameuid][key], str):
                savehook_new_data[gameuid][key] = [savehook_new_data[gameuid][key]]
            formLayout.addRow(
                (showname),
                listediterline(
                    showname,
                    showname,
                    savehook_new_data[gameuid][key],
                    ispathsedit=dict(filter1=filt),
                ),
            )

        for showname, key, filt in [
            ("sqlite翻译记录", "gamesqlitefile", "*.sqlite"),
        ]:
            formLayout.addRow(
                showname,
                getsimplepatheditor(
                    savehook_new_data[gameuid][key],
                    False,
                    False,
                    filt,
                    functools.partial(selectimg, gameuid, key),
                    True,
                ),
            )

    def gettransoptimi(self, formLayout: LFormLayout, gameuid):

        vbox = self.createfollowdefault(
            savehook_new_data[gameuid], "transoptimi_followdefault", formLayout
        )

        for item in static_data["transoptimi"]:
            name = item["name"]
            visname = item["visname"]
            if checkpostlangmatch(name):
                setting = loadpostsettingwindowmethod_private(name)
                if not setting:
                    continue

                def __(_f, _1, gameuid):
                    return _f(_1, gameuid)

                vbox.addRow(
                    visname,
                    getboxlayout(
                        [
                            getsimpleswitch(savehook_new_data[gameuid], name + "_use"),
                            getIconButton(
                                callback=functools.partial(__, setting, self, gameuid),
                                icon="fa.gear",
                            ),
                            QLabel(),
                            getsimpleswitch(
                                savehook_new_data[gameuid], name + "_merge"
                            ),
                            LLabel("继承默认"),
                        ],
                        makewidget=True,
                        margin0=True,
                    ),
                )

    def gettextproc(self, formLayout: LFormLayout, gameuid):

        vbox = self.createfollowdefault(
            savehook_new_data[gameuid], "textproc_follow_default", formLayout
        )

        model = LStandardItemModel()
        model.setHorizontalHeaderLabels(["预处理方法", "使用", "设置"])

        table = TableViewW()

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode((QAbstractItemView.SelectionMode.SingleSelection))
        table.setWordWrap(False)
        table.setModel(model)

        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self.__privatetextproc_showmenu)
        self.__textprocinternaltable = table
        self.__textprocinternalmodel = model
        self.__privatetextproc_gameuid = gameuid
        for row, k in enumerate(
            savehook_new_data[gameuid]["save_text_process_info"]["rank"]
        ):  # 2
            self.__checkaddnewmethod(row, k)
        vbox.addWidget(table)
        buttons = threebuttons(texts=["添加行", "删除行", "上移", "下移"])
        buttons.btn1clicked.connect(self.__privatetextproc_btn1)
        buttons.btn2clicked.connect(self.removerows)
        buttons.btn3clicked.connect(
            functools.partial(self.__privatetextproc_moverank, -1)
        )
        buttons.btn4clicked.connect(
            functools.partial(self.__privatetextproc_moverank, 1)
        )
        vbox.addWidget(buttons)
        vbox.addWidget(buttons)

    def __privatetextproc_showmenu(self, p):
        r = self.__textprocinternaltable.currentIndex().row()
        if r < 0:
            return
        menu = QMenu(self.__textprocinternaltable)
        remove = LAction(("删除"))
        up = LAction("上移")
        down = LAction("下移")
        menu.addAction(remove)
        menu.addAction(up)
        menu.addAction(down)
        action = menu.exec(self.__textprocinternaltable.cursor().pos())

        if action == remove:
            self.__privatetextproc_btn2()
        elif action == up:
            self.__privatetextproc_moverank(-1)
        elif action == down:
            self.__privatetextproc_moverank(1)

    def __privatetextproc_moverank(self, dy):
        __row = self.__textprocinternaltable.currentIndex().row()

        __list = savehook_new_data[self.__privatetextproc_gameuid][
            "save_text_process_info"
        ]["rank"]
        game = __list[__row]
        idx1 = __list.index(game)
        idx2 = (idx1 + dy) % len(__list)
        __list.insert(idx2, __list.pop(idx1))
        self.__textprocinternalmodel.removeRow(idx1)
        self.__checkaddnewmethod(idx2, game)
        self.__textprocinternaltable.setCurrentIndex(
            self.__textprocinternalmodel.index(__row, 0)
        )

    def __checkaddnewmethod(self, row, _internal):
        self.__textprocinternalmodel.insertRow(
            row,
            [
                QStandardItem(postprocessconfig[_internal]["name"]),
                QStandardItem(),
                QStandardItem(),
            ],
        )
        __dict = savehook_new_data[self.__privatetextproc_gameuid][
            "save_text_process_info"
        ]["postprocessconfig"]
        if _internal not in __dict:
            __dict[_internal] = postprocessconfig[_internal]
            __dict[_internal]["use"] = True
        btn = maybehavebutton(self, self.__privatetextproc_gameuid, _internal)

        self.__textprocinternaltable.setIndexWidget(
            self.__textprocinternalmodel.index(row, 1),
            getsimpleswitch(__dict[_internal], "use"),
        )
        if btn:
            self.__textprocinternaltable.setIndexWidget(
                self.__textprocinternalmodel.index(row, 2),
                btn,
            )

    def removerows(self):

        skip = []
        for index in self.__textprocinternaltable.selectedIndexes():
            if index.row() in skip:
                continue
            skip.append(index.row())
        skip = reversed(sorted(skip))

        for row in skip:
            self.__textprocinternalmodel.removeRow(row)
            _dict = savehook_new_data[self.__privatetextproc_gameuid][
                "save_text_process_info"
            ]
            post = _dict["rank"][row]
            _dict["rank"].pop(row)
            if post in _dict["postprocessconfig"]:
                _dict["postprocessconfig"].pop(post)

    def __privatetextproc_btn2(self):
        row = self.__textprocinternaltable.currentIndex().row()
        if row < 0:
            return
        self.__textprocinternalmodel.removeRow(row)
        _dict = savehook_new_data[self.__privatetextproc_gameuid][
            "save_text_process_info"
        ]
        post = _dict["rank"][row]
        _dict["rank"].pop(row)
        if post in _dict["postprocessconfig"]:
            _dict["postprocessconfig"].pop(post)

    def __privatetextproc_btn1(self):

        __viss = []
        _internal = []
        for xx in postprocessconfig:
            __list = savehook_new_data[self.__privatetextproc_gameuid][
                "save_text_process_info"
            ]["rank"]
            if xx in __list:
                continue
            __viss.append(postprocessconfig[xx]["name"])
            _internal.append(xx)

        def __callback(_internal, d):
            __ = _internal[d["k"]]
            __list.insert(0, __)
            self.__checkaddnewmethod(0, __)

        __d = {"k": 0}
        autoinitdialog(
            self,
            ("预处理方法"),
            400,
            [
                {
                    "type": "combo",
                    "name": ("预处理方法"),
                    "d": __d,
                    "k": "k",
                    "list": __viss,
                },
                {
                    "type": "okcancel",
                    "callback": functools.partial(__callback, _internal, __d),
                },
            ],
        )

    def getlangtab(self, formLayout: LFormLayout, gameuid):

        savehook_new_data[gameuid]["private_tgtlang_2"] = savehook_new_data[
            gameuid
        ].get("private_tgtlang_2", globalconfig["tgtlang4"])
        savehook_new_data[gameuid]["private_srclang_2"] = savehook_new_data[
            gameuid
        ].get("private_srclang_2", globalconfig["srclang4"])

        formLayout2 = self.createfollowdefault(
            savehook_new_data[gameuid], "lang_follow_default", formLayout
        )
        formLayout2.addRow(
            "源语言",
            getsimplecombobox(
                static_data["language_list_translator"],
                savehook_new_data[gameuid],
                "private_srclang_2",
                internal=static_data["language_list_translator_inner"],
            ),
        )
        formLayout2.addRow(
            "目标语言",
            getsimplecombobox(
                static_data["language_list_translator"],
                savehook_new_data[gameuid],
                "private_tgtlang_2",
                internal=static_data["language_list_translator_inner"],
            ),
        )

    def gethooktab(self, formLayout: LFormLayout, gameuid):

        formLayout.addRow(
            "延迟注入(ms)",
            getspinbox(0, 1000000, savehook_new_data[gameuid], "inserthooktimeout"),
        )

        formLayout.addRow(
            "特殊码",
            listediterline(
                ("特殊码"),
                ("特殊码"),
                savehook_new_data[gameuid]["needinserthookcode"],
            ),
        )

        for k in [
            "codepage_index",
            "removeuseless",
            "direct_filterrepeat",
            "textthreaddelay",
            "maxBufferSize",
            "maxHistorySize",
            "filter_chaos_code",
            "use_yapi",
        ]:
            if k not in savehook_new_data[gameuid]["hooksetting_private"]:
                savehook_new_data[gameuid]["hooksetting_private"][k] = globalconfig[k]

        formLayout2 = self.createfollowdefault(
            savehook_new_data[gameuid],
            "hooksetting_follow_default",
            formLayout,
            lambda: gobject.baseobject.textsource.setsettings(),
        )
        formLayout2.addRow(
            "代码页",
            getsimplecombobox(
                static_data["codepage_display"],
                savehook_new_data[gameuid]["hooksetting_private"],
                "codepage_index",
                lambda x: gobject.baseobject.textsource.setsettings(),
            ),
        )
        formLayout2.addRow(
            "过滤反复刷新的句子",
            getsimpleswitch(
                savehook_new_data[gameuid]["hooksetting_private"],
                "direct_filterrepeat",
                callback=lambda x: gobject.baseobject.textsource.setsettings(),
            ),
        )

        formLayout2.addRow(
            "移除非选定hook",
            getsimpleswitch(
                savehook_new_data[gameuid]["hooksetting_private"], "removeuseless"
            ),
        )
        formLayout2.addRow(
            "刷新延迟(ms)",
            getspinbox(
                0,
                10000,
                savehook_new_data[gameuid]["hooksetting_private"],
                "textthreaddelay",
                callback=lambda x: gobject.baseobject.textsource.setsettings(),
            ),
        )
        formLayout2.addRow(
            "最大缓冲区长度",
            getspinbox(
                0,
                1000000,
                savehook_new_data[gameuid]["hooksetting_private"],
                "maxBufferSize",
                callback=lambda x: gobject.baseobject.textsource.setsettings(),
            ),
        )
        formLayout2.addRow(
            "最大缓存文本长度",
            getspinbox(
                0,
                1000000000,
                savehook_new_data[gameuid]["hooksetting_private"],
                "maxHistorySize",
                callback=lambda x: gobject.baseobject.textsource.setsettings(),
            ),
        )
        formLayout2.addRow(
            "过滤包含乱码的文本行",
            getsimpleswitch(
                savehook_new_data[gameuid]["hooksetting_private"],
                "filter_chaos_code",
            ),
        )
        formLayout2.addRow(
            "使用YAPI注入",
            getsimpleswitch(
                savehook_new_data[gameuid]["hooksetting_private"],
                "use_yapi",
            ),
        )


@Singleton_close
class dialog_setting_game(QDialog):

    def __init__(self, parent, gameuid, setindexhook=0) -> None:
        super().__init__(parent, Qt.WindowType.WindowCloseButtonHint)
        global _global_dialog_setting_game
        _global_dialog_setting_game = self

        self.setWindowTitle(savehook_new_data[gameuid]["title"])

        self.setWindowIcon(getExeIcon(uid2gamepath[gameuid], cache=True))
        _ = dialog_setting_game_internal(self, gameuid)
        _.methodtab.setCurrentIndex(setindexhook)
        _.setMinimumSize(QSize(600, 500))
        l = QHBoxLayout(self)
        self.setLayout(l)
        l.addWidget(_)
        l.setContentsMargins(0, 0, 0, 0)
        self.show()
        try:
            self.setGeometry(
                calculate_centered_rect(
                    _global_dialog_savedgame_new.parent().parent().geometry(),
                    self.size(),
                )
            )
        except:
            pass


@Singleton_close
class dialog_syssetting(LDialog):

    def __init__(self, parent, type_=1) -> None:
        super().__init__(parent, Qt.WindowType.WindowCloseButtonHint)
        self.setWindowTitle("其他设置")
        formLayout = LFormLayout(self)

        formLayout.addRow(
            "隐藏不存在的游戏",
            getsimpleswitch(globalconfig, "hide_not_exists"),
        )
        if type_ == 1:
            for key, name in [
                ("itemw", "宽度"),
                ("itemh", "高度"),
                # ("imgw", "图片宽度"),
                # ("imgh", "图片高度"),
                ("margin", "边距"),
                ("textH", "文字区高度"),
            ]:
                formLayout.addRow(
                    name,
                    getspinbox(0, 1000, globalconfig["dialog_savegame_layout"], key),
                )
        elif type_ == 2:
            for key, name in [
                ("listitemheight", "文字区高度"),
                ("listitemwidth", "高度"),
            ]:
                formLayout.addRow(
                    name,
                    getspinbox(0, 1000, globalconfig["dialog_savegame_layout"], key),
                )

        for key, key2, name in [
            ("backcolor1", "transparent", "颜色"),
            ("onselectcolor1", "transparentselect", "选中时颜色"),
            ("onfilenoexistscolor1", "transparentnotexits", "游戏不存在时颜色"),
        ]:
            formLayout.addRow(
                name,
                getcolorbutton(
                    globalconfig["dialog_savegame_layout"],
                    key,
                    callback=functools.partial(
                        selectcolor,
                        self,
                        globalconfig["dialog_savegame_layout"],
                        key,
                        None,
                        self,
                        key,
                    ),
                    name=key,
                    parent=self,
                ),
            )
            formLayout.addRow(
                name + "_" + "不透明度",
                getspinbox(0, 100, globalconfig["dialog_savegame_layout"], key2),
            )
        if type_ == 1:
            formLayout.addRow(
                "缩放",
                getsimplecombobox(
                    ["填充", "适应", "拉伸", "居中"],
                    globalconfig,
                    "imagewrapmode",
                ),
            )
        formLayout.addRow(
            "启动游戏不修改顺序",
            getsimpleswitch(globalconfig, "startgamenototop"),
        )

        if type_ == 1:
            formLayout.addRow(
                "显示标题",
                getsimpleswitch(globalconfig, "showgametitle"),
            )
        self.show()


@threader
def startgame(gameuid):
    try:
        game = uid2gamepath[gameuid]
        if os.path.exists(game):
            mode = savehook_new_data[gameuid]["onloadautochangemode2"]
            if mode > 0:
                _ = {1: "texthook", 2: "copy", 3: "ocr"}
                if globalconfig["sourcestatus2"][_[mode]]["use"] == False:
                    globalconfig["sourcestatus2"][_[mode]]["use"] = True

                    yuitsu_switch(
                        gobject.baseobject.settin_ui,
                        globalconfig["sourcestatus2"],
                        "sourceswitchs",
                        _[mode],
                        None,
                        True,
                    )
                    gobject.baseobject.starttextsource(use=_[mode], checked=True)

            localeswitchedrun(gameuid)

    except:
        print_exc()


def opendirforgameuid(gameuid):
    f = uid2gamepath[gameuid]
    f = os.path.dirname(f)
    if os.path.exists(f) and os.path.isdir(f):
        os.startfile(f)


def __b64string(a: str):
    return hashlib.md5(a.encode("utf8")).hexdigest()


def __scaletosize(_pix: QPixmap, tgt):

    if min(_pix.width(), _pix.height()) > 400:

        if _pix.height() < 400:
            sz = QSize(_pix.width() * 400 // _pix.height(), 400)
        else:
            sz = QSize(400, _pix.height() * 400 // _pix.width())
        _pix = _pix.scaled(
            sz,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    _pix.save(tgt)


def _getcachedimage(src, small):
    if not small:
        _pix = QPixmap(src)
        if _pix.isNull():
            return None
        return _pix
    if not os.path.exists(src):
        return None
    src2 = gobject.getcachedir(f"icon2/{__b64string(src)}.jpg")
    _pix = QPixmap(src2)
    if not _pix.isNull():
        return _pix
    _pix = QPixmap(src)
    if _pix.isNull():
        return None
    __scaletosize(_pix, src2)
    return _pix


def _getpixfunction(kk, small=False):
    if (
        savehook_new_data[kk]["currentmainimage"]
        in savehook_new_data[kk]["imagepath_all"]
    ):
        src = savehook_new_data[kk]["currentmainimage"]
        pix = _getcachedimage(src, small)
        if pix:
            return pix
    for _ in savehook_new_data[kk]["imagepath_all"]:
        pix = _getcachedimage(_, small)
        if pix:
            return pix
    _pix = getExeIcon(uid2gamepath[kk], False, cache=True)
    return _pix


def startgamecheck(self, gameuid):
    if not gameuid:
        return
    if not os.path.exists(uid2gamepath[gameuid]):
        return
    if globalconfig["startgamenototop"] == False:
        idx = savehook_new_list.index(gameuid)
        savehook_new_list.insert(0, savehook_new_list.pop(idx))
    self.parent().parent().close()
    startgame(gameuid)


def addgamesingle(parent, callback, targetlist):
    f = QFileDialog.getOpenFileName(options=QFileDialog.Option.DontResolveSymlinks)

    res = f[0]
    if res == "":
        return
    res = os.path.normpath(res)
    uid = find_or_create_uid(targetlist, res)
    if uid in targetlist:
        idx = targetlist.index(uid)
        response = QMessageBox.question(
            parent,
            "",
            _TR("游戏已存在，是否重复添加？"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if response == QMessageBox.StandardButton.No:
            if idx == 0:
                return
            targetlist.pop(idx)
        else:
            uid = duplicateconfig(uid)
    targetlist.insert(0, uid)
    callback(uid)


def addgamebatch(callback, targetlist):
    res = QFileDialog.getExistingDirectory(
        options=QFileDialog.Option.DontResolveSymlinks
    )
    if res == "":
        return
    for _dir, _, _fs in os.walk(res):
        for _f in _fs:
            path = os.path.normpath(os.path.abspath(os.path.join(_dir, _f)))
            if path.lower().endswith(".exe") == False:
                continue
            uid = find_or_create_uid(targetlist, path)
            if uid in targetlist:
                targetlist.pop(targetlist.index(uid))
            targetlist.insert(0, uid)
            callback(uid)


@Singleton_close
class dialog_savedgame_integrated(saveposwindow):

    def selectlayout(self, type):
        try:
            globalconfig["gamemanager_integrated_internal_layout"] = type
            klass = [
                dialog_savedgame_new,
                dialog_savedgame_v3,
                dialog_savedgame_lagacy,
            ][type]

            [self.layout1btn, self.layout2btn, self.layout3btn][(type) % 3].setEnabled(
                False
            )
            [self.layout1btn, self.layout2btn, self.layout3btn][
                (type + 1) % 3
            ].setEnabled(False)
            [self.layout1btn, self.layout2btn, self.layout3btn][
                (type + 2) % 3
            ].setEnabled(False)
            [self.layout1btn, self.layout2btn, self.layout3btn][
                (type + 1) % 3
            ].setChecked(False)
            [self.layout1btn, self.layout2btn, self.layout3btn][
                (type + 2) % 3
            ].setChecked(False)
            _old = self.internallayout.takeAt(0).widget()
            _old.hide()
            _ = klass(self)
            self.internallayout.addWidget(_)
            _.directshow()
            _old.deleteLater()
            [self.layout1btn, self.layout2btn, self.layout3btn][
                (type + 1) % 3
            ].setEnabled(True)
            [self.layout1btn, self.layout2btn, self.layout3btn][
                (type + 2) % 3
            ].setEnabled(True)
        except:
            print_exc()

    def __init__(self, parent) -> None:
        super().__init__(
            parent,
            flags=Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint,
            poslist=globalconfig["savegamedialoggeo"],
        )
        self.setWindowTitle("游戏管理")
        self.setWindowIcon(qtawesome.icon("fa.gear"))
        w, self.internallayout = getboxlayout(
            [], margin0=True, makewidget=True, both=True
        )

        self.internallayout.addWidget(QWidget())
        self.setCentralWidget(w)
        self.layout1btn = MySwitch(self, icon="fa.th")
        self.layout2btn = MySwitch(self, icon="fa.th-list")
        self.layout3btn = MySwitch(self, icon="fa.list")
        self.layout1btn.clicked.connect(functools.partial(self.selectlayout, 0))
        self.layout2btn.clicked.connect(functools.partial(self.selectlayout, 1))
        self.layout3btn.clicked.connect(functools.partial(self.selectlayout, 2))
        self.layout1btn.setFixedSize(QSize(20, 20))
        self.layout2btn.setFixedSize(QSize(20, 20))
        self.layout3btn.setFixedSize(QSize(20, 20))
        self.show()
        self.selectlayout(globalconfig["gamemanager_integrated_internal_layout"])

    def resizeEvent(self, e: QResizeEvent):
        self.layout1btn.move(e.size().width() - self.layout1btn.width(), 0)
        self.layout2btn.move(
            e.size().width() - self.layout2btn.width() - self.layout1btn.width(), 0
        )
        self.layout3btn.move(
            e.size().width()
            - self.layout3btn.width()
            - self.layout2btn.width()
            - self.layout1btn.width(),
            0,
        )


def calculatetagidx(tagid):
    i = 0
    for save in savegametaged:
        if save is None and tagid is None:
            return i
        elif save and tagid and save["uid"] == tagid:
            return i
        i += 1

    return None


def getreflist(reftagid):
    _idx = calculatetagidx(reftagid)
    if _idx is None:
        return None
    tag = savegametaged[_idx]
    if tag is None:
        return savehook_new_list
    return tag["games"]


class dialog_savedgame_new(QWidget):
    def clicked2(self):
        try:
            game = self.currentfocusuid
            idx2 = self.reflist.index(game)
            self.reflist.pop(idx2)

            idx2 = self.idxsave.index(game)
            self.flow.removeidx(idx2)
            self.idxsave.pop(idx2)
            ItemWidget.clearfocus()
            try:
                self.flow.widget(idx2).click()
            except:
                self.flow.widget(idx2 - 1).click()

        except:
            print_exc()

    def clicked4(self):
        opendirforgameuid(self.currentfocusuid)

    def addgame(self, uid):
        if uid not in self.idxsave:
            self.newline(uid, first=True)
        else:
            idx = self.idxsave.index(uid)
            self.idxsave.pop(idx)
            self.idxsave.insert(0, uid)
            self.flow.totop1(idx)

    def clicked3_batch(self):
        addgamebatch(self.addgame, self.reflist)

    def clicked3(self):
        addgamesingle(self, self.addgame, self.reflist)

    def tagschanged(self, tags):
        self.currtags = tags
        newtags = tags
        self.idxsave.clear()
        ItemWidget.clearfocus()
        self.formLayout.removeWidget(self.flow)
        self.flow.hide()
        self.flow.deleteLater()
        self.flow = lazyscrollflow()
        self.flow.bgclicked.connect(ItemWidget.clearfocus)
        self.formLayout.insertWidget(self.formLayout.count() - 1, self.flow)
        idx = 0

        for k in self.reflist:
            if newtags != self.currtags:
                break
            notshow = False
            for tag, _type, _ in tags:
                if _type == tagitem.TYPE_EXISTS:
                    if os.path.exists(uid2gamepath[k]) == False:
                        notshow = True
                        break
                elif _type == tagitem.TYPE_DEVELOPER:
                    if tag not in savehook_new_data[k]["developers"]:
                        notshow = True
                        break
                elif _type == tagitem.TYPE_TAG:
                    if tag not in savehook_new_data[k]["webtags"]:
                        notshow = True
                        break
                elif _type == tagitem.TYPE_USERTAG:
                    if tag not in savehook_new_data[k]["usertags"]:
                        notshow = True
                        break
                elif _type == tagitem.TYPE_RAND:
                    if (
                        tag not in savehook_new_data[k]["webtags"]
                        and tag not in savehook_new_data[k]["usertags"]
                        and tag not in savehook_new_data[k]["title"]
                        and tag not in savehook_new_data[k]["developers"]
                    ):
                        notshow = True
                        break
            if notshow:
                continue
            self.newline(k, idx == 0)
            idx += 1
        self.flow.directshow()

    def showmenu(self, p):
        menu = QMenu(self)

        editname = LAction(("修改列表名称"))
        addlist = LAction(("创建列表"))
        dellist = LAction(("删除列表"))

        startgame = LAction(("开始游戏"))
        delgame = LAction(("删除游戏"))
        opendir = LAction(("打开目录"))
        addtolist = LAction(("添加到列表"))
        gamesetting = LAction(("游戏设置"))
        addgame = LAction(("添加游戏"))
        batchadd = LAction(("批量添加"))
        othersetting = LAction(("其他设置"))

        if self.currentfocusuid:
            exists = os.path.exists(uid2gamepath[self.currentfocusuid])
            if exists:
                menu.addAction(startgame)
            if exists:
                menu.addAction(opendir)
            menu.addAction(gamesetting)
            menu.addAction(delgame)
            menu.addSeparator()
            menu.addAction(addtolist)
        else:
            if self.reftagid:
                menu.addAction(editname)
            menu.addAction(addlist)
            if self.reftagid:
                menu.addAction(dellist)
            menu.addSeparator()
            menu.addAction(addgame)
            menu.addAction(batchadd)
            menu.addSeparator()
            menu.addAction(othersetting)
        action = menu.exec(self.mapToGlobal(p))
        if action == startgame:
            startgamecheck(self, self.currentfocusuid)
        elif action == gamesetting:
            self.showsettingdialog()
        elif action == addtolist:
            self.addtolist()
        elif action == delgame:
            self.clicked2()
        elif action == opendir:
            self.clicked4()
        elif action == addgame:
            self.clicked3()
        elif action == batchadd:
            self.clicked3_batch()
        elif action == othersetting:
            dialog_syssetting(self)

        elif action == editname or action == addlist:
            _dia = Prompt_dialog(
                self,
                "修改列表名称" if action == editname else "创建列表",
                "",
                [
                    [
                        "名称",
                        (
                            savegametaged[calculatetagidx(self.reftagid)]["title"]
                            if action == editname
                            else ""
                        ),
                    ],
                ],
            )

            if _dia.exec():

                title = _dia.text[0].text()
                if title != "":
                    i = calculatetagidx(self.reftagid)
                    if action == addlist:
                        tag = {
                            "title": title,
                            "games": [],
                            "uid": str(uuid.uuid4()),
                            "opened": True,
                        }
                        savegametaged.insert(i, tag)
                        self.loadcombo(False)
                    elif action == editname:

                        savegametaged[i]["title"] = title
                        self.loadcombo(False)
        elif action == dellist:
            i = calculatetagidx(self.reftagid)
            savegametaged.pop(i)
            self.loadcombo(False)
            self.resetcurrvislist(globalconfig["currvislistuid"])

    def directshow(self):
        self.flow.directshow()

    def resetcurrvislist(self, uid):
        self.reftagid = uid
        self.reflist = getreflist(uid)
        self.tagschanged(self.currtags)

    def loadcombo(self, init):
        vis, uid = loadvisinternal()
        if not init:
            w = self.__layout.itemAt(0).widget()
            self.__layout.removeWidget(w)
            w.hide()
            w.deleteLater()
        self.__layout.insertWidget(
            0,
            getsimplecombobox(
                vis,
                globalconfig,
                "currvislistuid",
                self.resetcurrvislist,
                internal=uid,
                static=True,
            ),
        )

    def __init__(self, parent) -> None:
        super().__init__(parent)
        global _global_dialog_savedgame_new
        _global_dialog_savedgame_new = self
        formLayout = QVBoxLayout()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.__layout = layout
        self.loadcombo(True)
        self.reflist = getreflist(globalconfig["currvislistuid"])
        self.reftagid = globalconfig["currvislistuid"]

        def refreshcombo():
            _ = self.tagswidget.lineEdit.currentText()
            self.tagswidget.lineEdit.clear()
            self.tagswidget.lineEdit.addItems(globalconfig["labelset"])
            self.tagswidget.lineEdit.setCurrentText(_)

        layout.addWidget(
            getIconButton(
                lambda: listediter(
                    parent,
                    ("标签集"),
                    ("标签"),
                    globalconfig["labelset"],
                    closecallback=refreshcombo,
                ),
                icon="fa.gear",
            ),
        )

        def callback(t):
            if t in globalconfig["labelset"]:
                tp = tagitem.TYPE_USERTAG
            else:
                tp = tagitem.TYPE_RAND
            self.tagswidget.addTag(t, tp)

            self.tagswidget.lineEdit.clear()
            self.tagswidget.lineEdit.addItems(globalconfig["labelset"])
            self.tagswidget.lineEdit.clearEditText()

        self.tagswidget = TagWidget(self)
        self.tagswidget.lineEdit.addItems(globalconfig["labelset"])
        self.tagswidget.lineEdit.setCurrentText("")
        self.tagswidget.linepressedenter.connect(callback)
        self.currtags = tuple()
        self.tagswidget.tagschanged.connect(self.tagschanged)
        _ = QLabel()
        _.setFixedWidth(60)
        layout.addWidget(self.tagswidget)
        layout.addWidget(_)
        formLayout.addLayout(layout)
        self.flow = QWidget()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showmenu)
        formLayout.addWidget(self.flow)
        self.formLayout = formLayout
        buttonlayout = QHBoxLayout()
        self.buttonlayout = buttonlayout
        self.savebutton = []
        self.simplebutton(
            "开始游戏", True, lambda: startgamecheck(self, self.currentfocusuid), True
        )
        self.simplebutton("游戏设置", True, self.showsettingdialog, False)
        self.simplebutton("删除游戏", True, self.clicked2, False)
        self.simplebutton("打开目录", True, self.clicked4, True)

        self.simplebutton("添加到列表", True, self.addtolist, False)
        if globalconfig["startgamenototop"]:
            self.simplebutton("左移", True, functools.partial(self.moverank, -1), False)
            self.simplebutton("右移", True, functools.partial(self.moverank, 1), False)
        self.simplebutton("添加游戏", False, self.clicked3, 1)
        self.simplebutton("批量添加", False, self.clicked3_batch, 1)
        self.simplebutton("其他设置", False, lambda: dialog_syssetting(self), False)
        formLayout.addLayout(buttonlayout)
        self.idxsave = []
        self.setLayout(formLayout)
        self.activategamenum = 1
        self.itemfocuschanged(False, None)
        if globalconfig["hide_not_exists"]:
            self.tagswidget.addTag(_TR("存在"), tagitem.TYPE_EXISTS)
        else:
            self.tagschanged(tuple())

        class WindowEventFilter(QObject):
            def eventFilter(__, obj, event):
                try:
                    if obj == self:
                        global _global_dialog_setting_game
                        _global_dialog_setting_game.raise_()
                except:
                    pass
                return False

        self.__filter = WindowEventFilter()  # keep ref
        self.installEventFilter(self.__filter)

    def addtolist(self):
        getalistname(
            self,
            lambda x: self.addtolistcallback(x, self.currentfocusuid),
            True,
            self.reftagid,
        )

    def addtolistcallback(self, uid, gameuid):
        if gameuid not in getreflist(uid):
            getreflist(uid).insert(0, gameuid)
        else:
            idx = getreflist(uid).index(gameuid)
            getreflist(uid).insert(0, getreflist(uid).pop(idx))

    def moverank(self, dx):
        game = self.currentfocusuid

        idx1 = self.idxsave.index(game)
        idx2 = (idx1 + dx) % len(self.idxsave)
        game2 = self.idxsave[idx2]
        self.idxsave.insert(idx2, self.idxsave.pop(idx1))
        self.flow.switchidx(idx1, idx2)

        idx1 = self.reflist.index(game)
        idx2 = self.reflist.index(game2)
        self.reflist.insert(idx2, self.reflist.pop(idx1))

    def showsettingdialog(self):
        try:
            dialog_setting_game(self.parent(), self.currentfocusuid)
        except:
            print_exc()

    def simplebutton(self, text, save, callback, exists):
        button5 = LPushButton(text)
        button5.setMinimumWidth(10)
        if save:
            self.savebutton.append((button5, exists))
        button5.clicked.connect(callback)
        button5.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.buttonlayout.addWidget(button5)
        return button5

    def itemfocuschanged(self, b, k):

        if b:
            self.currentfocusuid = k
        else:
            self.currentfocusuid = None

        for _btn, exists in self.savebutton:
            _able1 = b and (
                (not exists)
                or (self.currentfocusuid)
                and (os.path.exists(uid2gamepath[self.currentfocusuid]))
            )
            _btn.setEnabled(_able1)

    def getagameitem(self, k, focus):
        gameitem = ItemWidget(
            k, functools.partial(_getpixfunction, k), savehook_new_data[k]["title"]
        )
        gameitem.doubleclicked.connect(functools.partial(startgamecheck, self))
        gameitem.focuschanged.connect(self.itemfocuschanged)
        if focus:
            gameitem.click()
        return gameitem

    def newline(self, k, first=False):

        itemw = globalconfig["dialog_savegame_layout"]["itemw"]
        itemh = globalconfig["dialog_savegame_layout"]["itemh"]

        if first:
            self.idxsave.insert(0, k)
            self.flow.insertwidget(
                0, (functools.partial(self.getagameitem, k, True), QSize(itemw, itemh))
            )
        else:
            self.idxsave.append(k)
            self.flow.addwidget(
                (functools.partial(self.getagameitem, k, False), QSize(itemw, itemh))
            )


class LazyLoadTableView(TableViewW):
    def __init__(self, model: LStandardItemModel) -> None:
        super().__init__()
        self.widgetfunction = []
        self.lock = threading.Lock()
        self.setModel(model)
        self.started = False

    def starttraceir(self):
        self.started = True
        self.model().rowsRemoved.connect(functools.partial(self.insertremove))
        self.model().rowsInserted.connect(functools.partial(self.insert))

    def resizeEvent(self, e):
        self.loadVisibleRows()
        super().resizeEvent(e)

    def insertremove(self, index, start, end):
        off = end - start + 1
        with self.lock:
            collect = []
            for i in range(len(self.widgetfunction)):
                if self.widgetfunction[i][0] > end:
                    self.widgetfunction[i][0] -= off
                elif (
                    self.widgetfunction[i][0] >= start
                    and self.widgetfunction[i][0] <= end
                ):
                    collect.append(i)
            for i in collect:
                self.widgetfunction.pop(i)

        self.loadVisibleRows()

    def insert(self, index, start, end):
        off = end - start + 1
        with self.lock:
            for i in range(len(self.widgetfunction)):
                if self.widgetfunction[i][0] >= start:
                    self.widgetfunction[i][0] += off
                    # print(self.widgetfunction[i])

        self.loadVisibleRows()

    def setIndexWidget(self, index: QModelIndex, widgetf):
        if not self.started:
            self.widgetfunction.append([index.row(), index.column(), widgetf])
            return
        if self.visualRect(index).intersects(self.viewport().rect()):
            w = widgetf()
            super().setIndexWidget(index, w)
        else:
            with self.lock:
                self.widgetfunction.append([index.row(), index.column(), widgetf])

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        self.loadVisibleRows()

    def loadVisibleRows(self):
        with self.lock:
            collect = []
            for i, index in enumerate(self.widgetfunction):
                row, col, wf = index
                if self.visualRect(self.model().index(row, col)).intersects(
                    self.viewport().rect()
                ):
                    collect.insert(0, i)

            for i in collect:
                row, col, wf = self.widgetfunction.pop(i)

                w = wf()
                super().setIndexWidget(self.model().index(row, col), w)


class dialog_savedgame_lagacy(QWidget):

    def directshow(self):
        pass

    def showsettingdialog(self, k):
        dialog_setting_game(self, k)

    def clicked2(self):
        try:

            idx = self.table.currentIndex().row()
            savehook_new_list.pop(idx)
            self.savelist.pop(idx)
            self.model.removeRow(self.table.currentIndex().row())
        except:
            pass

    def clicked3(self):
        def call(uid):
            if uid in self.savelist:
                idx = self.savelist.index(uid)
                self.savelist.pop(idx)
                self.model.removeRow(idx)
            self.newline(0, uid)
            self.table.setCurrentIndex(self.model.index(0, 0))

        addgamesingle(self, call, savehook_new_list)

    def clicked(self):
        startgamecheck(
            self, self.model.item(self.table.currentIndex().row(), 2).savetext
        )

    def delayloadicon(self, k):
        return getcolorbutton(
            "",
            "",
            functools.partial(opendirforgameuid, k),
            qicon=getExeIcon(uid2gamepath[k], cache=True),
        )

    def callback_leuse(self, k, use):
        if use:
            savehook_new_data[k]["launch_method"] = None
        else:
            savehook_new_data[k]["launch_method"] = "direct"

    def newline(self, row, k):
        keyitem = QStandardItem()
        keyitem.savetext = k
        self.model.insertRow(
            row,
            [
                QStandardItem(),
                QStandardItem(),
                keyitem,
                QStandardItem((savehook_new_data[k]["title"])),
            ],
        )
        self.table.setIndexWidget(
            self.model.index(row, 0),
            D_getsimpleswitch(
                {"1": savehook_new_data[k].get("launch_method") != "direct"},
                "1",
                callback=functools.partial(self.callback_leuse, k),
            ),
        )
        self.table.setIndexWidget(
            self.model.index(row, 1),
            functools.partial(self.delayloadicon, k),
        )

        self.table.setIndexWidget(
            self.model.index(row, 2),
            D_getIconButton(
                functools.partial(self.showsettingdialog, k), icon="fa.gear"
            ),
        )

    def __init__(self, parent) -> None:
        # if dialog_savedgame._sigleton :
        #         return
        # dialog_savedgame._sigleton=True
        super().__init__(parent)

        formLayout = QVBoxLayout(self)  #
        model = LStandardItemModel()
        model.setHorizontalHeaderLabels(["转区", "", "设置", "游戏"])  # ,'HOOK'])

        self.model = model

        table = LazyLoadTableView(model)
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        table.horizontalHeader().setStretchLastSection(True)
        # table.setEditTriggers(QAbstractItemView.NoEditTriggers);
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode((QAbstractItemView.SelectionMode.SingleSelection))
        table.setWordWrap(False)
        self.table = table
        self.savelist = []
        for row, k in enumerate(savehook_new_list):  # 2
            self.newline(row, k)
            self.savelist.append(k)
        self.table.starttraceir()
        bottom = QHBoxLayout()

        button = LPushButton("开始游戏")
        self.button = button
        button.clicked.connect(self.clicked)
        button3 = LPushButton("添加游戏")

        button3.clicked.connect(self.clicked3)
        button2 = LPushButton("删除游戏")

        button2.clicked.connect(self.clicked2)
        bottom.addWidget(button)
        bottom.addWidget(button2)
        bottom.addWidget(button3)
        _ = QLabel()
        _.setFixedHeight(20)
        _.setStyleSheet("background: transparent;")
        formLayout.addWidget(_)
        formLayout.addWidget(table)
        formLayout.addLayout(bottom)


class clickitem(QWidget):
    focuschanged = pyqtSignal(bool, str)
    doubleclicked = pyqtSignal(str)
    globallashfocus = None

    @classmethod
    def clearfocus(cls):
        try:  # 可能已被删除
            if clickitem.globallashfocus:
                clickitem.globallashfocus.focusOut()
        except:
            pass
        clickitem.globallashfocus = None

    def mouseDoubleClickEvent(self, e):
        self.doubleclicked.emit(self.uid)

    def click(self):
        try:
            self.bottommask.setStyleSheet(
                f'background-color: {str2rgba(globalconfig["dialog_savegame_layout"]["onselectcolor1"],globalconfig["dialog_savegame_layout"]["transparentselect"])};'
            )
            if self != clickitem.globallashfocus:
                clickitem.clearfocus()
            clickitem.globallashfocus = self
            self.focuschanged.emit(True, self.uid)
        except:
            print_exc()

    def mousePressEvent(self, ev) -> None:
        self.click()

    def focusOut(self):
        self.bottommask.setStyleSheet("background-color: rgba(255,255,255, 0);")
        self.focuschanged.emit(False, self.uid)

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.bottommask.resize(a0.size())
        self.maskshowfileexists.resize(a0.size())
        self.bottomline.resize(a0.size())

    def __init__(self, uid):
        super().__init__()

        self.uid = uid
        self.lay = QHBoxLayout()
        self.lay.setSpacing(0)
        self.lay.setContentsMargins(0, 0, 0, 0)

        self.maskshowfileexists = QLabel(self)

        c = globalconfig["dialog_savegame_layout"][
            ("onfilenoexistscolor1", "backcolor1")[os.path.exists(uid2gamepath[uid])]
        ]
        c = str2rgba(
            c,
            globalconfig["dialog_savegame_layout"][
                ("transparentnotexits", "transparent")[
                    os.path.exists(uid2gamepath[uid])
                ]
            ],
        )
        self.maskshowfileexists.setStyleSheet(f"background-color:{c};")
        self.bottommask = QLabel(self)
        self.bottommask.setStyleSheet("background-color: rgba(255,255,255, 0);")
        _ = QLabel(self)
        _.setStyleSheet(
            """background-color: rgba(255,255,255, 0);border-bottom: 1px solid gray;"""
        )
        self.bottomline = _
        size = globalconfig["dialog_savegame_layout"]["listitemheight"]
        _ = QLabel()
        _.setFixedSize(QSize(size, size))
        _.setScaledContents(True)
        _.setStyleSheet("background-color: rgba(255,255,255, 0);")
        icon = _getpixfunction(
            uid, small=True
        )  # getExeIcon(uid2gamepath[uid], icon=False, cache=True)
        icon.setDevicePixelRatio(self.devicePixelRatioF())
        _.setPixmap(icon)
        self.lay.addWidget(_)
        _ = QLabel(savehook_new_data[uid]["title"])
        _.setWordWrap(True)
        _.setFixedHeight(size + 1)
        self.lay.addWidget(_)
        self.setLayout(self.lay)
        _.setStyleSheet("""background-color: rgba(255,255,255, 0);""")


class fadeoutlabel(QLabel):
    def __init__(self, p=None):
        super().__init__(p)

        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)

        self.setStyleSheet("""background-color: rgba(255,255,255, 0);""")
        self.animation = QPropertyAnimation(effect, b"opacity")
        self.animation.setDuration(4000)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setDirection(QPropertyAnimation.Direction.Forward)

    def setText(self, t):
        super().setText(t)
        self.animation.stop()
        self.animation.start()


class XQListWidget(QListWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def sethor(self, hor):
        if hor:
            self.setFlow(QListWidget.LeftToRight)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.setFlow(QListWidget.TopToBottom)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)


def getselectpos(parent, callback):
    __d = {"k": 0}
    __vis, __uid = ["下", "右", "上", "左"], [0, 1, 2, 3]

    def __wrap(callback, __d, __uid):
        if len(__uid) == 0:
            return

        uid = __uid[__d["k"]]
        callback(uid)

    if len(__uid) > 1:
        autoinitdialog(
            parent,
            "位置",
            600,
            [
                {
                    "type": "combo",
                    "name": "位置",
                    "d": __d,
                    "k": "k",
                    "list": __vis,
                },
                {
                    "type": "okcancel",
                    "callback": functools.partial(__wrap, callback, __d, __uid),
                },
            ],
        )
    else:
        callback(__uid[0])


class previewimages(QWidget):
    changepixmappath = pyqtSignal(str)
    removepath = pyqtSignal(str)

    def sethor(self, hor):
        self.hor = hor
        self.list.sethor(hor)

        if self.hor:
            self.list.setIconSize(QSize(self.height(), self.height()))
        else:
            self.list.setIconSize(QSize(self.width(), self.width()))

    def sizeHint(self):
        return QSize(100, 100)

    def __init__(self, p) -> None:
        super().__init__(p)
        self.lay = QHBoxLayout()
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.list = XQListWidget(self)
        self.list.currentRowChanged.connect(self._visidx)
        self.lay.addWidget(self.list)
        self.setLayout(self.lay)

    def tolastnext(self, dx):
        if self.list.count() == 0:
            return self.list.setCurrentRow(-1)
        self.list.setCurrentRow((self.list.currentRow() + dx) % self.list.count())

    def setpixmaps(self, paths, currentpath):
        self.list.setCurrentRow(-1)
        self.list.blockSignals(True)
        self.list.clear()
        pathx = []
        for path in paths:
            image = _getcachedimage(path, True)
            if image is None:
                continue
            item = QListWidgetItem()
            item.imagepath = path
            pathx.append(path)
            item.setIcon(QIcon(image))

            self.list.addItem(item)
        self.list.blockSignals(False)
        pixmapi = 0
        if currentpath in pathx:
            pixmapi = pathx.index(currentpath)
        self.list.setCurrentRow(pixmapi)

    def _visidx(self, _):
        item = self.list.currentItem()
        if item is None:
            pixmap_ = None
        else:
            pixmap_ = item.imagepath
        self.changepixmappath.emit(pixmap_)

    def removecurrent(self, delfile):
        idx = self.list.currentRow()
        item = self.list.currentItem()
        if item is None:
            return
        path = item.imagepath
        self.removepath.emit(path)
        self.list.takeItem(idx)
        if delfile:
            try:
                os.remove(path)
            except:
                pass

    def resizeEvent(self, e: QResizeEvent):
        if self.hor:
            self.list.setIconSize(QSize(self.height(), self.height()))
        else:
            self.list.setIconSize(QSize(self.width(), self.width()))
        return super().resizeEvent(e)


class hoverbtn(LLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        self.clicked.emit()
        return super().mousePressEvent(a0)

    def __init__(self, *argc):
        super().__init__(*argc)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def resizeEvent(self, e):
        style = r"""QLabel{
                background: transparent; 
                border-radius:0;
                font-size: %spx;
                color:transparent; 
            }
            QLabel:hover{
                background-color: rgba(255,255,255,0.5); 
                color:black;
            }""" % (
            min(self.height(), self.width()) // 3
        )
        self.setStyleSheet(style)
        super().resizeEvent(e)


class viewpixmap_x(QWidget):
    tolastnext = pyqtSignal(int)
    startgame = pyqtSignal()
    switchstop = pyqtSignal()

    def sizeHint(self):
        return QSize(400, 400)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.pixmapviewer = pixmapviewer(self)
        self.leftclick = hoverbtn("<-", self)
        self.rightclick = hoverbtn("->", self)
        self.maybehavecomment = hoverbtn(self)
        self.bottombtn = hoverbtn("开始游戏", self)
        self.bottombtn.clicked.connect(self.startgame)
        self.leftclick.clicked.connect(lambda: self.tolastnext.emit(-1))
        self.rightclick.clicked.connect(lambda: self.tolastnext.emit(1))
        self.maybehavecomment.clicked.connect(self.viscomment)
        self.commentedit = QPlainTextEdit(self)
        self.commentedit.textChanged.connect(self.changecommit)
        self.timenothide = QLabel(self)
        self.timenothide.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pathandopen = QPushButton(self)
        self.pathandopen.clicked.connect(
            lambda: (
                os.startfile(os.path.abspath(self.currentimage))
                if self.currentimage
                else ""
            )
        )
        self.centerwidget = QWidget(self)
        self.centerwidgetlayout = QVBoxLayout()
        audio = QHBoxLayout()
        self.recordbtn = statusbutton(
            icons=["fa.microphone", "fa.stop"], colors=["", ""]
        )
        self.recordbtn.statuschanged.connect(self.startorendrecord)
        self.centerwidget.setLayout(self.centerwidgetlayout)
        self.centerwidgetlayout.addWidget(self.timenothide)
        self.centerwidgetlayout.addWidget(self.pathandopen)
        self.centerwidgetlayout.addWidget(self.commentedit)
        self.centerwidgetlayout.addLayout(audio)
        audio.addWidget(self.recordbtn)
        self.btnplay = statusbutton(icons=["fa.play", "fa.stop"], colors=["", ""])
        audio.addWidget(self.btnplay)
        self.btnplay.statuschanged.connect(self.playorstop)
        gobject.baseobject.hualang_recordbtn = self.recordbtn
        self.centerwidget.setVisible(False)
        self.pathview = fadeoutlabel(self)
        self.infoview = fadeoutlabel(self)
        self.infoview.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.currentimage = None
        self.play_context = None
        self.recorder = None
        self.switchstop.connect(self.switchstop_f)

    def switchstop_f(self):
        if self.play_context:
            self.btnplay.click()

    def checkplayable(self):
        if not self.currentimage:
            return False
        mp3 = extradatas.get("imagerefmp3", {}).get(self.currentimage, None)
        if mp3 is None:
            return False
        if not os.path.exists(mp3):
            return False
        return True

    def playorstop(self, idx):
        if not self.checkplayable():
            return
        mp3 = extradatas["imagerefmp3"][self.currentimage]
        if idx == 1:
            self.play_context = playonce(mp3, globalconfig["ttscommon"]["volume"])
            self.sigtime = time.time()

            def __(tm):
                while self.play_context and self.play_context.isplaying:
                    time.sleep(1)
                if self.sigtime == tm:
                    self.switchstop.emit()

            threading.Thread(target=__, args=(self.sigtime,)).start()
        else:
            if not self.play_context:
                return
            self.play_context = None

    def startorendrecord(self, idx):
        if idx == 1:
            if self.play_context:
                self.btnplay.click()
            self.btnplay.setEnabled(False)
            self.recorder = loopbackrecorder()
        else:
            self.btnplay.setEnabled(False)

            def _cb(image, path):
                if not image:
                    return
                tgt = image + os.path.splitext(path)[1]
                shutil.copy(path, tgt)
                if "imagerefmp3" not in extradatas:
                    extradatas["imagerefmp3"] = {}
                extradatas["imagerefmp3"][image] = tgt

                self.btnplay.setEnabled(self.checkplayable())

            if not self.recorder:
                return
            self.recorder.end(callback=functools.partial(_cb, self.currentimage))
            self.recorder = None

    def changecommit(self):
        if "imagecomment" not in extradatas:
            extradatas["imagecomment"] = {}
        extradatas["imagecomment"][self.currentimage] = self.commentedit.toPlainText()

    def viscomment(self):
        self.centerwidget.setVisible(not self.centerwidget.isVisible())

    def resizeEvent(self, e: QResizeEvent):
        self.pixmapviewer.resize(e.size())
        self.pathview.resize(e.size().width(), self.pathview.height())
        self.infoview.resize(e.size().width(), self.infoview.height())
        self.leftclick.setGeometry(
            0, e.size().height() // 5, e.size().width() // 5, 3 * e.size().height() // 5
        )
        self.bottombtn.setGeometry(
            e.size().width() // 5,
            4 * e.size().height() // 5,
            3 * e.size().width() // 5,
            e.size().height() // 5,
        )
        self.rightclick.setGeometry(
            4 * e.size().width() // 5,
            e.size().height() // 5,
            e.size().width() // 5,
            3 * e.size().height() // 5,
        )
        self.maybehavecomment.setGeometry(
            e.size().width() // 5, 0, 3 * e.size().width() // 5, e.size().height() // 5
        )
        self.centerwidget.setGeometry(
            e.size().width() // 5,
            e.size().height() // 5,
            3 * e.size().width() // 5,
            3 * e.size().height() // 5,
        )
        super().resizeEvent(e)

    def changepixmappath(self, path):
        if self.recorder:
            self.recordbtn.click()
        if self.play_context:
            self.btnplay.click()

        self.currentimage = path
        self.centerwidget.setVisible(False)
        self.pathandopen.setText(path)
        self.pathview.setText(path)
        try:
            timestamp = get_time_stamp(ct=os.path.getctime(path), ms=False)
        except:
            timestamp = None
        self.infoview.setText(timestamp)
        self.commentedit.setPlainText(extradatas.get("imagecomment", {}).get(path, ""))
        self.timenothide.setText(timestamp)
        if not path:
            pixmap = QPixmap()
        else:
            pixmap = QPixmap.fromImage(QImage(path))
            if pixmap is None or pixmap.isNull():
                pixmap = QPixmap()
        self.pixmapviewer.showpixmap(pixmap)
        self.btnplay.setEnabled(self.checkplayable())


class pixwrapper(QWidget):
    startgame = pyqtSignal()

    def setrank(self, rank):
        if rank:
            self.spliter.addWidget(self.pixview)
            self.spliter.addWidget(self.previewimages)
        else:
            self.spliter.addWidget(self.previewimages)
            self.spliter.addWidget(self.pixview)

    def sethor(self, hor):
        if hor:

            self.spliter.setOrientation(Qt.Orientation.Vertical)
        else:

            self.spliter.setOrientation(Qt.Orientation.Horizontal)
        self.previewimages.sethor(hor)

    def __init__(self) -> None:
        super().__init__()
        rank = (globalconfig["viewlistpos"] // 2) == 0
        hor = (globalconfig["viewlistpos"] % 2) == 0

        self.previewimages = previewimages(self)
        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.pixview = viewpixmap_x(self)
        self.pixview.startgame.connect(self.startgame)
        self.spliter = QSplitter(self)
        self.vlayout.addWidget(self.spliter)
        self.setrank(rank)
        self.sethor(hor)
        self.pixview.tolastnext.connect(self.previewimages.tolastnext)
        self.setLayout(self.vlayout)
        self.previewimages.changepixmappath.connect(self.changepixmappath)
        self.previewimages.removepath.connect(self.removepath)
        self.k = None
        self.removecurrent = self.previewimages.removecurrent

        self.previewimages.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.previewimages.customContextMenuRequested.connect(
            functools.partial(self.menu, True)
        )
        self.pixview.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pixview.customContextMenuRequested.connect(
            functools.partial(self.menu, False)
        )

    def menu(self, _1, _):
        menu = QMenu(self)

        setimage = LAction(("设为封面"))
        deleteimage = LAction(("删除图片"))
        deleteimage_x = LAction(("删除图片文件"))
        hualang = LAction(("画廊"))
        pos = LAction(("位置"))

        menu.addAction(setimage)
        menu.addAction(deleteimage)
        menu.addAction(deleteimage_x)
        menu.addAction(hualang)
        if _1:
            menu.addSeparator()
            menu.addAction(pos)
        action = menu.exec(QCursor.pos())
        if action == deleteimage:
            self.removecurrent(False)
        elif action == deleteimage_x:
            self.removecurrent(True)
        elif action == pos:
            getselectpos(self, self.switchpos)

        elif action == hualang:
            listediter(
                self,
                ("画廊"),
                ("画廊"),
                savehook_new_data[self.k]["imagepath_all"],
                closecallback=lambda: self.setpix(self.k),
                ispathsedit=dict(),
            )
        elif action == setimage:
            curr = savehook_new_data[self.k]["currentvisimage"]
            savehook_new_data[self.k]["currentmainimage"] = curr

    def switchpos(self, pos):
        globalconfig["viewlistpos"] = pos
        rank = (globalconfig["viewlistpos"] // 2) == 0
        hor = (globalconfig["viewlistpos"] % 2) == 0
        self.setrank(rank)
        self.sethor(hor)

    def removepath(self, path):
        lst = savehook_new_data[self.k]["imagepath_all"]
        lst.pop(lst.index(path))

    def changepixmappath(self, path):
        if path:
            savehook_new_data[self.k]["currentvisimage"] = path
        self.pixview.changepixmappath(path)

    def setpix(self, k):
        self.k = k
        pixmaps = savehook_new_data[k]["imagepath_all"].copy()
        self.previewimages.setpixmaps(pixmaps, savehook_new_data[k]["currentvisimage"])


def loadvisinternal(skipid=False, skipidid=None):
    __vis = []
    __uid = []
    for _ in savegametaged:
        if _ is None:
            __vis.append("GLOBAL")
            __uid.append(None)
        else:
            __vis.append(_["title"])
            __uid.append(_["uid"])
        if skipid:
            if skipidid == __uid[-1]:
                __uid.pop(-1)
                __vis.pop(-1)
    return __vis, __uid


def getalistname(parent, callback, skipid=False, skipidid=None):
    __d = {"k": 0}
    __vis, __uid = loadvisinternal(skipid, skipidid)

    def __wrap(callback, __d, __uid):
        if len(__uid) == 0:
            return

        uid = __uid[__d["k"]]
        callback(uid)

    if len(__uid) > 1:
        autoinitdialog(
            parent,
            "目标",
            600,
            [
                {
                    "type": "combo",
                    "name": "目标",
                    "d": __d,
                    "k": "k",
                    "list": __vis,
                },
                {
                    "type": "okcancel",
                    "callback": functools.partial(__wrap, callback, __d, __uid),
                },
            ],
        )
    elif len(__uid):

        callback(__uid[0])


class dialog_savedgame_v3(QWidget):
    def viewitem(self, k):
        try:
            self.pixview.setpix(k)
            self.currentfocusuid = k
            currvis = self.righttop.currentIndex()
            if self.righttop.count() > 1:
                self.righttop.removeTab(1)
            tabadd_lazy(
                self.righttop,
                savehook_new_data[k]["title"],
                lambda v: v.addWidget(dialog_setting_game_internal(self, k)),
            )
            self.righttop.setCurrentIndex(currvis)
        except:
            print_exc()

    def itemfocuschanged(self, reftagid, b, k):

        self.reftagid = reftagid
        if b:
            self.currentfocusuid = k
        else:
            self.currentfocusuid = None

        for _btn, exists in self.savebutton:
            _able1 = b and (
                (not exists)
                or (self.currentfocusuid)
                and (os.path.exists(uid2gamepath[self.currentfocusuid]))
            )
            _btn.setEnabled(_able1)
        if self.currentfocusuid:
            self.viewitem(k)

    def delayitemcreater(self, k, select, reftagid):

        item = clickitem(k)
        item.doubleclicked.connect(functools.partial(startgamecheck, self))
        item.focuschanged.connect(functools.partial(self.itemfocuschanged, reftagid))
        if select:
            item.click()
        return item

    def newline(self, res):
        self.reallist[self.reftagid].insert(0, res)
        self.stack.w(calculatetagidx(self.reftagid)).insertw(
            0,
            functools.partial(
                self.delayitemcreater,
                res,
                True,
                self.reftagid,
            ),
            1 + globalconfig["dialog_savegame_layout"]["listitemheight"],
        )
        self.stack.directshow()

    def stack_showmenu(self, p):
        menu = QMenu(self)

        addlist = LAction(("创建列表"))
        startgame = LAction(("开始游戏"))
        delgame = LAction(("删除游戏"))
        opendir = LAction(("打开目录"))
        addtolist = LAction(("添加到列表"))
        if not self.currentfocusuid:

            menu.addAction(addlist)
        else:
            exists = os.path.exists(uid2gamepath[self.currentfocusuid])
            if exists:
                menu.addAction(startgame)
                menu.addAction(delgame)

                menu.addAction(opendir)

                menu.addSeparator()
                menu.addAction(addtolist)
            else:

                menu.addAction(addtolist)
                menu.addSeparator()
                menu.addAction(delgame)

        action = menu.exec(QCursor.pos())
        if action == startgame:
            startgamecheck(self, self.currentfocusuid)
        elif addlist == action:
            _dia = Prompt_dialog(
                self,
                "创建列表",
                "",
                [
                    ["名称", ""],
                ],
            )

            if _dia.exec():

                title = _dia.text[0].text()
                if title != "":
                    i = calculatetagidx(None)
                    if action == addlist:
                        tag = {
                            "title": title,
                            "games": [],
                            "uid": str(uuid.uuid4()),
                            "opened": True,
                        }
                        savegametaged.insert(i, tag)
                        group0 = self.createtaglist(self.stack, title, tag["uid"], True)
                        self.stack.insertw(i, group0)

        elif action == delgame:
            self.shanchuyouxi()
        elif action == opendir:
            self.clicked4()
        elif action == addtolist:
            self.addtolist()

    def addtolistcallback(self, uid, gameuid):

        __save = self.reftagid
        self.reftagid = uid

        if gameuid not in getreflist(self.reftagid):
            getreflist(self.reftagid).insert(0, gameuid)
            self.newline(gameuid)
        else:
            idx = getreflist(self.reftagid).index(gameuid)
            getreflist(self.reftagid).insert(0, getreflist(self.reftagid).pop(idx))
            self.stack.w(calculatetagidx(self.reftagid)).torank1(idx)
        self.reftagid = __save

    def addtolist(self):
        getalistname(
            self,
            lambda x: self.addtolistcallback(x, self.currentfocusuid),
            True,
            self.reftagid,
        )

    def directshow(self):
        self.stack.directshow()

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.currentfocusuid = None
        self.reftagid = None
        self.reallist = {}
        self.stack = stackedlist()
        self.stack.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.stack.customContextMenuRequested.connect(self.stack_showmenu)
        self.stack.setFixedWidth(
            globalconfig["dialog_savegame_layout"]["listitemwidth"]
        )
        self.stack.bgclicked.connect(clickitem.clearfocus)
        lay = QHBoxLayout()
        self.setLayout(lay)
        lay.addWidget(self.stack)
        lay.setSpacing(0)
        self.righttop = makesubtab_lazy()
        self.pixview = pixwrapper()
        self.pixview.startgame.connect(
            lambda: startgamecheck(self, self.currentfocusuid)
        )
        _w = QWidget()
        rightlay = QVBoxLayout()
        rightlay.setContentsMargins(0, 0, 0, 0)
        _w.setLayout(rightlay)
        self.righttop.addTab(_w, "画廊")
        lay.addWidget(self.righttop)
        rightlay.addWidget(self.pixview)
        self.buttonlayout = QHBoxLayout()
        self.savebutton = []
        rightlay.addLayout(self.buttonlayout)

        self.simplebutton(
            "开始游戏", True, lambda: startgamecheck(self, self.currentfocusuid), True
        )
        self.simplebutton("删除游戏", True, self.shanchuyouxi, False)
        self.simplebutton("打开目录", True, self.clicked4, True)
        self.simplebutton("添加到列表", True, self.addtolist, False)
        if globalconfig["startgamenototop"]:
            self.simplebutton("上移", True, functools.partial(self.moverank, -1), False)
            self.simplebutton("下移", True, functools.partial(self.moverank, 1), False)
        self.simplebutton("添加游戏", False, self.clicked3, 1)
        self.simplebutton("批量添加", False, self.clicked3_batch, 1)
        self.simplebutton(
            "其他设置", False, lambda: dialog_syssetting(self, type_=2), False
        )
        isfirst = True
        for i, tag in enumerate(savegametaged):
            # None
            # {
            #     "title":xxx
            #     "games":[]
            # }
            if tag is None:
                title = "GLOBAL"
                lst = savehook_new_list
                tagid = None
                opened = globalconfig["global_list_opened"]
            else:
                lst = tag["games"]
                title = tag["title"]
                tagid = tag["uid"]
                opened = tag.get("opened", True)
            group0 = self.createtaglist(self.stack, title, tagid, opened)
            self.stack.insertw(i, group0)
            rowreal = 0
            for row, k in enumerate(lst):
                if globalconfig["hide_not_exists"] and not os.path.exists(
                    uid2gamepath[k]
                ):
                    continue
                self.reallist[tagid].append(k)
                if opened and isfirst and (rowreal == 0):
                    vis = True
                    isfirst = False
                else:
                    vis = False
                group0.insertw(
                    rowreal,
                    functools.partial(self.delayitemcreater, k, vis, tagid),
                    1 + globalconfig["dialog_savegame_layout"]["listitemheight"],
                )

                rowreal += 1

    def taglistrerank(self, tagid, dx):
        idx1 = calculatetagidx(tagid)

        idx2 = (idx1 + dx) % len(savegametaged)
        savegametaged.insert(idx2, savegametaged.pop(idx1))
        self.stack.switchidx(idx1, idx2)

    def tagbuttonmenu(self, tagid):
        self.currentfocusuid = None
        self.reftagid = tagid
        menu = QMenu(self)
        editname = LAction(("修改列表名称"))
        addlist = LAction(("创建列表"))
        dellist = LAction(("删除列表"))
        Upaction = LAction("上移")
        Downaction = LAction("下移")
        addgame = LAction(("添加游戏"))
        batchadd = LAction(("批量添加"))
        menu.addAction(Upaction)
        menu.addAction(Downaction)
        menu.addSeparator()
        if tagid:
            menu.addAction(editname)
        menu.addAction(addlist)
        if tagid:
            menu.addAction(dellist)
        menu.addSeparator()
        menu.addAction(addgame)
        menu.addAction(batchadd)

        action = menu.exec(QCursor.pos())
        if action == addgame:
            self.clicked3()
        elif action == batchadd:
            self.clicked3_batch()
        elif action == Upaction:
            self.taglistrerank(tagid, -1)
        elif action == Downaction:
            self.taglistrerank(tagid, 1)
        elif action == editname or action == addlist:
            _dia = Prompt_dialog(
                self,
                "修改列表名称" if action == editname else "创建列表",
                "",
                [
                    [
                        "名称",
                        (
                            savegametaged[calculatetagidx(tagid)]["title"]
                            if action == editname
                            else ""
                        ),
                    ],
                ],
            )

            if _dia.exec():

                title = _dia.text[0].text()
                if title != "":
                    i = calculatetagidx(tagid)
                    if action == addlist:
                        tag = {
                            "title": title,
                            "games": [],
                            "uid": str(uuid.uuid4()),
                            "opened": True,
                        }
                        savegametaged.insert(i, tag)
                        group0 = self.createtaglist(self.stack, title, tag["uid"], True)
                        self.stack.insertw(i, group0)
                    elif action == editname:
                        self.stack.w(i).settitle(title)
                        savegametaged[i]["title"] = title

        elif action == dellist:
            i = calculatetagidx(tagid)
            savegametaged.pop(i)
            self.stack.popw(i)
            self.reallist.pop(tagid)

    def createtaglist(self, p, title, tagid, opened):

        self.reallist[tagid] = []
        _btn = QPushButton(title)
        _btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        _btn.clicked.connect(functools.partial(self._revertoepn, tagid))
        _btn.customContextMenuRequested.connect(
            functools.partial(self.tagbuttonmenu, tagid)
        )
        return shrinkableitem(p, _btn, opened)

    def _revertoepn(self, tagid):
        item = savegametaged[calculatetagidx(tagid)]
        if item is None:
            globalconfig["global_list_opened"] = not globalconfig["global_list_opened"]
        else:
            savegametaged[calculatetagidx(tagid)]["opened"] = not savegametaged[
                calculatetagidx(tagid)
            ]["opened"]

    def moverank(self, dx):
        uid = self.currentfocusuid
        idx1 = self.reallist[self.reftagid].index(uid)
        idx2 = (idx1 + dx) % len(self.reallist[self.reftagid])
        uid2 = self.reallist[self.reftagid][idx2]
        self.reallist[self.reftagid].insert(
            idx2, self.reallist[self.reftagid].pop(idx1)
        )

        self.stack.w(calculatetagidx(self.reftagid)).switchidx(idx1, idx2)
        idx1 = getreflist(self.reftagid).index(uid)
        idx2 = getreflist(self.reftagid).index(uid2)
        getreflist(self.reftagid).insert(idx2, getreflist(self.reftagid).pop(idx1))

    def shanchuyouxi(self):
        if not self.currentfocusuid:
            return

        try:
            uid = self.currentfocusuid
            idx2 = getreflist(self.reftagid).index(uid)
            getreflist(self.reftagid).pop(idx2)

            idx2 = self.reallist[self.reftagid].index(uid)
            self.reallist[self.reftagid].pop(idx2)
            clickitem.clearfocus()
            group0 = self.stack.w(calculatetagidx(self.reftagid))
            group0.popw(idx2)
            try:
                group0.w(idx2).click()
            except:
                group0.w(idx2 - 1).click()
        except:
            print_exc()

    def clicked4(self):
        opendirforgameuid(self.currentfocusuid)

    def addgame(self, uid):
        if uid not in self.reallist[self.reftagid]:
            self.newline(uid)
        else:
            idx = self.reallist[self.reftagid].index(uid)
            self.reallist[self.reftagid].pop(idx)
            self.reallist[self.reftagid].insert(0, uid)
            self.stack.w(calculatetagidx(self.reftagid)).torank1(idx)

    def clicked3_batch(self):
        addgamebatch(self.addgame, getreflist(self.reftagid))

    def clicked3(self):
        addgamesingle(self, self.addgame, getreflist(self.reftagid))

    def clicked(self):
        startgamecheck(self, self.currentfocusuid)

    def simplebutton(self, text, save, callback, exists):
        button5 = LPushButton(text)
        button5.setMinimumWidth(10)
        if save:
            self.savebutton.append((button5, exists))
        button5.clicked.connect(callback)
        button5.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.buttonlayout.addWidget(button5)
        return button5
