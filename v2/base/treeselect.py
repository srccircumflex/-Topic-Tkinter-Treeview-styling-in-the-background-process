from __future__ import annotations

from typing import Generator, Callable

import tkinter as tk
import tkinter.ttk as ttk

from re import Pattern, search, compile, IGNORECASE, error as ReError, escape
from typing import Literal, Any, Iterable
from pathlib import Path


class TagsConfig:
    t_entry = "t-entry"
    t_sector = "t-sector-is"
    t_top_sector = "t-sector-top"
    t_sub_sector = "t-sector-sub"
    c_check_entry = "c-check"
    c_uncheck_entry = "c-uncheck"
    c_check_sector = "c-check-sector"
    c_uncheck_sector = "c-uncheck-sector"
    c_cstate_sector = "c-cstate-sector"
    m_match_entry = "m-1-entry"
    m_match_sector = "m-1-sector"
    m_hint_sector = "m-2-sector"
    m_match_and_hint_sector = "m-3-sector"

    def __init__(
            self,
            match_entry: dict[Literal["foreground", "background", "font", "image"], Any] = None,
            match_sector: dict[Literal["foreground", "background", "font", "image"], Any] = None,
            match_hint_sector: dict[Literal["foreground", "background", "font", "image"], Any] = None,
            match_hint_and_match_sector: dict[Literal["foreground", "background", "font", "image"], Any] = None,
            uncheck_entry: dict[Literal["foreground", "background", "font", "image"], Any] = None,
            check_entry: dict[Literal["foreground", "background", "font", "image"], Any] = None,
            uncheck_sector: dict[Literal["foreground", "background", "font", "image"], Any] = None,
            check_sector: dict[Literal["foreground", "background", "font", "image"], Any] = None,
            cstate_sector: dict[Literal["foreground", "background", "font", "image"], Any] = None,
            type_entry: dict[Literal["foreground", "background", "font", "image"], Any] = None,
            type_sector: dict[Literal["foreground", "background", "font", "image"], Any] = None,
            type_top_sector: dict[Literal["foreground", "background", "font", "image"], Any] = None,
            type_sub_sector: dict[Literal["foreground", "background", "font", "image"], Any] = None,
    ):
        config = {
            TagsConfig.c_check_entry: check_entry,
            TagsConfig.c_uncheck_entry: uncheck_entry,
            TagsConfig.c_check_sector: check_sector,
            TagsConfig.c_uncheck_sector: uncheck_sector,
            TagsConfig.c_cstate_sector: cstate_sector,
            TagsConfig.m_match_entry: match_entry,
            TagsConfig.m_match_sector: match_sector,
            TagsConfig.m_hint_sector: match_hint_sector,
            TagsConfig.m_match_and_hint_sector: match_hint_and_match_sector,
            TagsConfig.t_entry: type_entry,
            TagsConfig.t_sector: type_sector,
            TagsConfig.t_top_sector: type_top_sector,
            TagsConfig.t_sub_sector: type_sub_sector,
        }
        self.config = {k: v for k, v in config.items() if v is not None}

    def configure(self, tree: ttk.Treeview):

        for tag, kw in self.config.items():
            # (Trial-and-Error knowledge)
            # If the PhotoImages are not saved in an attribute of the object, they are not displayed.
            # They are probably deleted in the process by the garbage collector.
            for itm in kw.items():
                attr = "_%s_%s" % (tag, itm[0])
                setattr(tree, attr, itm[1])
                kw[itm[0]] = getattr(tree, attr)

            tree.tag_configure(tag, **kw)

    def __or__(self, other: TagsConfig):
        new = TagsConfig()
        new.config = self.config | other.config
        return new


class StructureNode(tuple[str, str, Any, tuple, bool]):

    def __new__(cls, label: str, values: Any, *children: StructureNode, iid: str = None, checked: bool = False, opened: bool = False) -> StructureNode:
        new = tuple.__new__(cls, (iid or label, label, values, children, checked, opened))
        new.has_child = bool(children)
        return new

    def child_iter(self) -> Generator[str]:
        def gen():
            yield self[0]
            for c in self[3]:
                c: StructureNode
                ci = c.child_iter()
                for i in ci:
                    yield i
        return gen()


class ThreeItem(str):
    text: str
    image: Any
    values: list[Any] | tuple[Any, ...] | Literal[""]
    open: bool
    tags: str | list[str] | tuple[str, ...]
    is_sector: bool

    def __new__(
            cls,
            iid: str,
            text: str,
            image: Any,
            values: list[Any] | tuple[Any, ...] | Literal[""],
            open: bool,
            tags: str | list[str] | tuple[str, ...],
            is_sector: bool
    ):
        new = str.__new__(cls, iid)
        new.text = text
        new.image = image
        new.values = values
        new.open = open
        new.tags = tags
        new.is_sector = is_sector
        return new

    def to_dict(self):
        return {k: getattr(self, k) for k in self.__class__.__annotations__} | {"iid": str(self)}

    @staticmethod
    def from_dict(__attrdict) -> ThreeItem:
        return ThreeItem(**__attrdict)

    def __getnewargs__(self):
        return self, self.text, self.image, self.values, self.open, self.tags, self.is_sector


class SelectTree(ttk.Treeview):
    top_sector_iids: tuple[str, ...]
    sub_sector_iids: tuple[str, ...]
    all_sector_iids: tuple[str, ...]
    entry_iids: tuple[str, ...]

    def __init__(
            self,
            *structure: StructureNode,
            iid_sep: str = ".",
            tags_config: TagsConfig,
            master=None,
            width: int = None,
            **tk_kwargs
    ):
        ttk.Treeview.__init__(self, master, show="tree", **tk_kwargs)

        if width:
            self.set_width(width)

        tags_config.configure(self)

        top_sector_iids = list()
        sub_sector_iids = list()
        entry_iids = list()

        def make(struc, parent=""):
            for _struc in struc:
                if parent:
                    iid = parent + iid_sep + _struc[0]
                else:
                    iid = _struc[0]
                if _struc[3]:
                    if not parent:
                        top_sector_iids.append(iid)
                        tags = (TagsConfig.t_sector, TagsConfig.t_top_sector)
                    else:
                        sub_sector_iids.append(iid)
                        tags = (TagsConfig.t_sector, TagsConfig.t_sub_sector)
                    if _struc[4]:
                        tags += (TagsConfig.c_check_sector,)
                    else:
                        tags += (TagsConfig.c_uncheck_sector,)
                    self.insert(parent, text=_struc[1], values=_struc[2], index="end", iid=iid, tags=tags, open=_struc[5])
                    make(_struc[3], iid)
                else:
                    entry_iids.append(iid)
                    if _struc[4]:
                        tags = (TagsConfig.t_entry, TagsConfig.c_check_entry)
                    else:
                        tags = (TagsConfig.t_entry, TagsConfig.c_uncheck_entry)
                    self.insert(parent, text=_struc[1], values=_struc[2], index="end", iid=iid, tags=tags, open=_struc[5])

        make(structure)

        self.top_sector_iids = tuple(top_sector_iids)
        self.sub_sector_iids = tuple(sub_sector_iids)
        self.all_sector_iids = self.top_sector_iids + self.sub_sector_iids
        self.entry_iids = tuple(entry_iids)

    def set_width(self, width: int, minwidth: int = None):
        if minwidth:
            self.column("#0", width=width, minwidth=minwidth)
        else:
            self.column("#0", width=width)

    def toggle_recursive_expand(self, iid: str = "", expand: bool = None) -> bool:
        if expand is None:
            if not iid:
                expand = True
                for sector in self.top_sector_iids:
                    if self.item(sector, "open"):
                        expand = False
                        break
            else:
                expand = not self.item(iid, "open")
        for sector in self.all_sector_iids:
            if sector.startswith(iid):
                self.item(sector, open=expand)
        return expand

    def expand_for_match(self):
        def x(_iid=""):
            for t in self.item(_iid, "tags"):
                if t.startswith("m-"):
                    self.item(_iid, open=True)
            children = self.get_children(_iid)
            for _iid in children:
                x(_iid)
        x()

    def iid_by_event(self, event):
        return self.identify_row(event.y)

    def iid_by_selected(self):
        if s := self.selection():
            return s[0]
        return ""

    def set_selection(self, iid: str):
        self.selection_set(iid)

    def get_main_list(self, parent_iid: str = ""):
        _list = list()

        def add(_iid=parent_iid):
            _list.append(_iid)
            children = self.get_children(_iid)
            for _iid in children:
                _list.append(_iid)
                add(_iid)

        add()
        return _list[1:]

    def get_next_match(
            self,
            start_iid: str = None,
            parent_iid: str = "",
            scip_hints: bool = True,
            scip_sectors: bool = False,
            reverse: bool = False,
            back_to_begin: bool = False,
    ):
        if matches := self.get_matches(
            parent_iid, scip_hints, scip_sectors
        ):
            start_iid: ThreeItem | str
            if start_iid is None:
                start_iid = self.iid_by_selected()
            if reverse:
                matches.reverse()
            try:
                return matches[matches.index(start_iid) + 1]
            except IndexError:
                if back_to_begin:
                    return matches[0]
                else:
                    return
            except ValueError:
                main_list = self.get_main_list()
                if reverse:
                    main_list.reverse()
                for i in main_list[main_list.index(start_iid):]:
                    try:
                        return matches[matches.index(i)]
                    except ValueError:
                        pass
                if back_to_begin:
                    return matches[0]
                else:
                    return
        else:
            return False

    def selection_to_next_match(
            self,
            start_iid: str = None,
            parent_iid: str = "",
            scip_hints: bool = True,
            scip_sectors: bool = False,
            reverse: bool = False,
            back_to_begin: bool = False,
    ):
        if match := self.get_next_match(start_iid, parent_iid, scip_hints, scip_sectors, reverse, back_to_begin):
            self.set_selection(match)
            self.focus(match)
        return match

    @staticmethod
    def element_by_event(event):
        return event.widget.identify("element", event.x, event.y)

    def event_points_to(self, event, ref: Literal["image", "text", "indicator", ""] = None) -> Literal["image", "text", "indicator"] | None | bool:
        element = self.element_by_event(event)
        if "image" in element:
            e = "image"
        elif "text" in element:
            e = "text"
        elif "indicator" in element:
            e = "indicator"
        else:
            e = None
        if ref is not None:
            return (e or "") == ref
        else:
            return e

    def get_matches(self, parent_iid: str = "", scip_hints: bool = True, scip_sectors: bool = False) -> list[ThreeItem]:
        matches = list()
        if scip_sectors:
            def find(_iid=parent_iid):
                children = self.get_children(_iid)
                for _iid in children:
                    itm = self.get(_iid)
                    if TagsConfig.m_match_entry in itm.tags:
                        matches.append(itm)
                    else:
                        find(_iid)
        elif scip_hints:
            def find(_iid=parent_iid):
                children = self.get_children(_iid)
                for _iid in children:
                    itm = self.get(_iid)
                    if (
                            TagsConfig.m_match_entry in itm.tags
                            or TagsConfig.m_match_sector in itm.tags
                            or TagsConfig.m_match_and_hint_sector in itm.tags
                    ):
                        matches.append(itm)
                    find(_iid)
        else:
            def find(_iid=parent_iid):
                children = self.get_children(_iid)
                for _iid in children:
                    itm = self.get(_iid)
                    for t in itm.tags:
                        if t.startswith("m-"):
                            matches.append(itm)
                    find(_iid)
        find()
        return matches

    def _change_check_tag(self, iid: str, tag: str):
        tags = set(self.item(iid, "tags"))
        for t in tags:
            if t.startswith("c-"):
                tags.remove(t)
                break
        tags.add(tag)
        self.item(iid, tags=tuple(tags))

    def _reset_match_tag(self, iid: str):
        tags = set(self.item(iid, "tags"))
        for t in tags:
            if t.startswith("m-"):
                tags.remove(t)
                break
        self.item(iid, tags=tuple(tags))

    def _add_match_tag(self, iid: str, tag: str):
        tags = set(self.item(iid, "tags"))
        for t in tags:
            if t.startswith("m-"):
                tag = "m-%s%s" % (
                    str(int(t[2]) | int(tag[2])),
                    t[3:]
                )
                tags.remove(t)
                break

        tags.add(tag)
        self.item(iid, tags=tuple(tags))

    def remove_match_tags(self, parent_iid: str = ""):
        def rm(_iid=parent_iid):
            children = self.get_children(_iid)
            for _iid in children:
                self._reset_match_tag(_iid)
                rm(_iid)
        rm()

    def search(self, pattern: str | Pattern, parent_iid: str = "") -> bool:

        self.remove_match_tags()

        match = False

        def _search(_iid=parent_iid):
            nonlocal match
            children = self.get_children(_iid)
            for _iid in children:
                if search(pattern, self.item(_iid, "text")):

                    match = True

                    if _iid in self.all_sector_iids:
                        self._add_match_tag(_iid, TagsConfig.m_match_sector)
                    else:
                        self._add_match_tag(_iid, TagsConfig.m_match_entry)

                    def parentref(__iid=_iid):
                        parent = self.parent(__iid)
                        if parent:
                            self._add_match_tag(parent, TagsConfig.m_hint_sector)
                            parentref(parent)

                    parentref()

                _search(_iid)

        _search()

        return match

    def toggle_check(self, check: bool = None, iid: str = "") -> bool:
        if iid:
            if iid in self.all_sector_iids:
                tag_check = TagsConfig.c_check_sector
                tag_uncheck = TagsConfig.c_uncheck_sector
            else:
                tag_check = TagsConfig.c_check_entry
                tag_uncheck = TagsConfig.c_uncheck_entry

            if check is None:
                check = tag_check not in self.item(iid, "tags")

            if check:
                tag = tag_check
            else:
                tag = tag_uncheck

            self._change_check_tag(iid, tag)

            # self.toggle_parent_check(check, iid)

            def __toggle(_iid, _tag):
                self._change_check_tag(_iid, _tag)
                parent = self.parent(_iid)
                if parent:
                    children = self.get_children(parent)
                    states = set((TagsConfig.c_check_entry in (i := self.item(c, "tags")) or TagsConfig.c_check_sector in i or TagsConfig.c_cstate_sector in i) for c in children)
                    if all(states):
                        _tag = TagsConfig.c_check_sector
                    elif len(states) == 1:
                        _tag = TagsConfig.c_uncheck_sector
                    else:
                        _tag = TagsConfig.c_cstate_sector
                    __toggle(parent, _tag)

            __toggle(iid, tag)

        elif check is None:
            check = not all((TagsConfig.c_check_sector in self.item(c, "tags")) for c in self.get_children(iid))

        if check:
            tag_entry = TagsConfig.c_check_entry
            tag_sector = TagsConfig.c_check_sector
        else:
            tag_entry = TagsConfig.c_uncheck_entry
            tag_sector = TagsConfig.c_uncheck_sector

        # self.toggle_children_check(check, iid)

        def __toggle(_iid):
            children = self.get_children(_iid)
            for _iid in children:
                if _iid in self.all_sector_iids:
                    self._change_check_tag(_iid, tag_sector)
                else:
                    self._change_check_tag(_iid, tag_entry)
                __toggle(_iid)

        __toggle(iid)

        return check

    def toggle_single_check(self, check: bool = None, iid: str = "") -> bool:
        if check is None:
            check = not self.is_checked(iid)
        self.toggle_check(False)
        self.toggle_check(check, iid)
        return check

    def is_checked(self, iid: str) -> bool:
        tags = self.item(iid, "tags")
        return TagsConfig.c_check_entry in tags or TagsConfig.c_check_sector in tags

    def get(self, iid: str) -> ThreeItem:
        item = self.item(iid)
        tags = item["tags"]
        return ThreeItem(iid, **item, is_sector=TagsConfig.t_sector in tags)

    def get_checked(self) -> list[ThreeItem]:
        checked = list()

        def get(iid):
            nonlocal checked
            item = self.item(iid)
            tags = item["tags"]
            if TagsConfig.c_check_entry in tags:
                checked.append(ThreeItem(iid, **item, is_sector=False))
            elif TagsConfig.c_check_sector in tags:
                checked.append(ThreeItem(iid, **item, is_sector=True))
            elif TagsConfig.c_cstate_sector in tags:
                for child in self.get_children(iid):
                    get(child)

        for sector in self.get_children(""):
            get(sector)

        return checked


class SelectTreeWidget(ttk.Frame):
    widget_frame: ttk.Frame
    tree: SelectTree
    search_entry: ttk.Entry
    expand_button: ttk.Button

    confirm_frame: ttk.Frame | None
    cancel_button: ttk.Button | None
    confirm_button: ttk.Button | None

    mode: Literal["multi", "single", "single entry", "single sector"]

    def __init__(
            self,
            master,
            *structure: StructureNode,
            checked_iids: Iterable[StructureNode | str] = (),
            mode: Literal["multi", "single", "single entry", "single sector"],
            make_confirm_frame: bool = True,
            tags_config_update: TagsConfig = TagsConfig(
                match_entry=None,
                match_sector=None,
                match_hint_sector=None,
                match_hint_and_match_sector=None,
                check_entry=None,
                uncheck_entry=None,
                check_sector=None,
                uncheck_sector=None,
                cstate_sector=None,
                type_entry=dict(),
                type_sector=dict(),
                type_top_sector=dict(),
                type_sub_sector=dict(),
            ),
            ttk_styler: Callable[[ttk.Style], dict] | None = None
    ):
        ttk.Frame.__init__(self, master)

        self.widget_frame = ttk.Frame(self)

        self.mode = mode

        _folder = str(Path(__file__).parent)

        self.tree = SelectTree(
            *structure,
            tags_config=TagsConfig(
                match_entry={'background': "#FFF84B", 'foreground': "black"},
                match_sector={'background': "#FFF84B", 'foreground': "black"},
                match_hint_sector={'background': "#DCFF4B"},
                match_hint_and_match_sector={'background': "#FFB84B"},
                check_entry=dict(image=tk.PhotoImage(file=_folder + "/dat/checkbox_checked18.png", master=self.widget_frame)),
                uncheck_entry=dict(image=tk.PhotoImage(file=_folder + "/dat/checkbox_unchecked18.png", master=self.widget_frame)),
                check_sector=dict(image=tk.PhotoImage(file=_folder + "/dat/checkbox_checked18.png", master=self.widget_frame)),
                uncheck_sector=dict(image=tk.PhotoImage(file=_folder + "/dat/checkbox_unchecked18.png", master=self.widget_frame)),
                cstate_sector=dict(image=tk.PhotoImage(file=_folder + "/dat/checkbox_hover18.png", master=self.widget_frame)),
            ) | tags_config_update,
            master=self.widget_frame
        )
        if self.mode == "multi":

            def check(e, iid=None):
                if iid:
                    self.tree.toggle_check(iid=iid)
                elif self.tree.event_points_to(e, "image"):
                    self.tree.toggle_check(iid=self.tree.iid_by_event(e))

        elif self.mode == "single":

            def check(e, iid=None):
                if iid:
                    self.tree.toggle_single_check(iid=iid)
                elif self.tree.event_points_to(e, "image"):
                    self.tree.toggle_single_check(iid=self.tree.iid_by_event(e))

        elif self.mode == "single entry":

            def check(e, iid=None):
                if iid:
                    if iid not in self.tree.all_sector_iids:
                        self.tree.toggle_single_check(iid=iid)
                elif self.tree.event_points_to(e, "image"):
                    iid = self.tree.iid_by_event(e)
                    if iid not in self.tree.all_sector_iids:
                        self.tree.toggle_single_check(iid=iid)

        elif self.mode == "single sector":

            def check(e, iid=None):
                if iid:
                    if iid in self.tree.all_sector_iids:
                        self.tree.toggle_single_check(iid=iid)
                elif self.tree.event_points_to(e, "image"):
                    iid = self.tree.iid_by_event(e)
                    if iid in self.tree.all_sector_iids:
                        self.tree.toggle_single_check(iid=iid)

        else:
            raise ValueError(self.mode)

        self.tree.bind("<Button-1>", check, add=True)
        self.tree.bind("<Double-Button-1>", lambda e: (check(e, iid) if (iid := self.tree.iid_by_selected()) not in self.tree.all_sector_iids else None))
        self.tree.bind("<Double-Right>", lambda e: self.tree.toggle_recursive_expand(self.tree.iid_by_selected(), True))
        self.tree.bind("<Double-Left>", lambda e: self.tree.toggle_recursive_expand(self.tree.iid_by_selected(), False))
        self.tree.bind("+", lambda e: self.tree.toggle_recursive_expand(self.tree.iid_by_selected(), True))
        self.tree.bind("-", lambda e: self.tree.toggle_recursive_expand(self.tree.iid_by_selected(), False))
        self.tree.bind("<Return>", lambda e: (check(e, self.tree.iid_by_selected()) if e.state == 16 else None))
        self.tree.bind("<space>", lambda e: (check(e, self.tree.iid_by_selected()) if e.state == 16 else None))
        self.tree.bind("#", lambda e: check(e, self.tree.iid_by_selected()))

        self.search_entry = ttk.Entry(
            master=self.widget_frame,
        )

        def _search(e):
            pattern = self.search_entry.get()
            if pattern:
                try:
                    pattern = compile(pattern, IGNORECASE)
                except ReError:
                    pattern = compile(escape(pattern), IGNORECASE)
                if self.tree.search(pattern):
                    self.tree.toggle_recursive_expand(expand=False)
                    self.tree.expand_for_match()
            else:
                self.tree.remove_match_tags()

        def delete(e):
            self.search_entry.delete(0, 9_999_999)
            self.tree.remove_match_tags()

        self.search_entry.bind("<Return>", _search)
        self.search_entry.bind("<Control-BackSpace>", delete)
        self.search_entry.bind("<Down>", lambda _: self.tree.focus_set())

        button = ttk.Button(
            master=self.widget_frame,
            text="ᐅ",
            width=2,
        )

        def expand(e):
            if self.tree.toggle_recursive_expand():
                button.configure(text="ᐁ")
            else:
                button.configure(text="ᐅ")

        button.bind("<Button-1>", expand)

        self.expand_button = button

        match_end__reverse_mode = [False, False]

        def next_match(
            reverse: bool
        ):
            if to_begin := (match_end__reverse_mode[0] and reverse == match_end__reverse_mode[1]):
                match_end__reverse_mode[0] = False
            if m := self.tree.selection_to_next_match(
                reverse=reverse,
                back_to_begin=to_begin,
            ):
                self.tree.focus_set()
            match_end__reverse_mode[0], match_end__reverse_mode[1] = m is None, reverse

        self.tree.bind("<F3>", lambda _: next_match(False))
        self.tree.bind("<Shift-F3>", lambda _: next_match(True))

        self.search_entry.bind("<F3>", lambda _: (_search(None), next_match(False)))
        self.search_entry.bind("<Shift-F3>", lambda _: (_search(None), next_match(True)))

        self.tree.bind("x", expand)
        master.bind("<Control-f>", lambda _: self.search_entry.focus_set())

        self.search_entry.grid(row=0, column=0, sticky=tk.NSEW)
        self.expand_button.grid(row=0, column=1, sticky=tk.NSEW)
        self.tree.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)

        self.widget_frame.grid(row=0, column=0)

        if make_confirm_frame:
            self.confirm_frame = ttk.Frame(self)
            self.cancel_button = ttk.Button(self.confirm_frame, text="Cancel")
            self.confirm_button = ttk.Button(self.confirm_frame, text="Confirm")
            self.cancel_button.pack(side="left", expand=True)
            self.confirm_button.pack(side="left", expand=True)
            self.confirm_frame.grid(row=1, column=0, sticky=tk.NSEW)
        else:
            self.confirm_frame = None
            self.cancel_button = None
            self.confirm_button = None

        for iid in checked_iids:
            if isinstance(iid, StructureNode):
                for _iid in iid.child_iter():
                    self.tree.toggle_check(True, _iid)
            else:
                self.tree.toggle_check(True, iid)

        self.expand_button.configure(style="expand.TButton")
        self.cancel_button.configure(style="cancel.TButton")
        self.confirm_button.configure(style="confirm.TButton")
        self.tree.configure(style="select.Treeview")

        if ttk_styler is not None:
            gl = globals()
            gl |= {"." + k: v for k, v in ttk_styler(ttk.Style()).items()}

    def resize(self, height: int, width: int) -> bool:
        """returns whether Tk-sizing is ready"""
        if self.confirm_frame:
            confirm_frame_geo = self.confirm_frame.winfo_geometry()
            if confirm_frame_geo.startswith("1x1"):
                return False
            height -= int(confirm_frame_geo.split("+")[0].split("x")[1]) // 10
            self.cancel_button.configure(width=width // 2 - 1)
            self.confirm_button.configure(width=width // 2 - 1)

        self.search_entry.configure(width=width - 2)
        self.tree.set_width(width)
        entry_height = int(self.search_entry.winfo_geometry().split("x")[1].split("+")[0])
        self.tree.configure(height=height - entry_height)
        return True

