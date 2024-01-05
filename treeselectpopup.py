from __future__ import annotations

from typing import Literal, Iterable

import tkinter.ttk as ttk
from tkinter import font as tkFont

from base.popup import PopupRoot
from base.server import TkBgServer, TkBgReceiver
from base.treeselect import StructureNode, SelectTreeWidget, TagsConfig


def popup(
        *structure: StructureNode,
        checked_iids: Iterable[StructureNode | str] = (),
        check_mode: Literal[
            "multi",
            "single",
            "single entry",
            "single sector",
        ] = "multi",
        at_focus_out: Literal["cancel", "confirm"] = None,
        window_mode: Literal["dead", "headless", "fullscreen", "top"] = False,
        window_title: str = "Tree Select",
        window_height: int = 70,
        window_width: int = 50,
        server_address: str = "127.0.0.11",
        server_port: int = 50_000,
        server_daemon: bool = True,
        return_mode: Literal[
            "receiver",
            "wait value",
            "instand value",
            "value at action"
        ] = "wait value",
        tags_config_update: TagsConfig = TagsConfig(),
        default_styling: bool = True
) -> TkBgReceiver | object:

    @TkBgServer(
        address=server_address,
        port=server_port,
        daemon=server_daemon,
        instand_return=return_mode in ("wait value", "instand value", "value at action"),
        instand_return_blocking=return_mode in ("wait value", "value at action"),
    )
    def func(server: TkBgServer, window_width=window_width, window_height=window_height):

        root = PopupRoot(
            window_mode=window_mode,
            title=window_title
        )
        if root.window_mode == "fullscreen":
            window_width, window_height = root.fullscreen_width, root.fullscreen_height

        widget = SelectTreeWidget(
            root,
            *structure,
            mode=check_mode,
            checked_iids=checked_iids,
            tags_config_update=tags_config_update,
        )
        widget.pack()

        def sizing(e):
            if not widget.resize(window_height, window_width):
                return

            root.resize(window_height, window_width)

            children = widget.tree.get_children()
            if children:
                widget.tree.selection_set(children[0])
                widget.tree.focus_set()
                widget.tree.focus(children[0])

            root.unbind(sizing_b)

        sizing_b = root.bind("<Configure>", sizing)

        def fin(obj):
            server.send(obj)
            server.exit()

        def cancel(e):
            fin(None)

        widget.cancel_button.bind("<Button-1>", cancel)
        widget.cancel_button.bind("<Return>", cancel)
        widget.cancel_button.bind("<space>", cancel)
        root.bind("<Escape>", cancel)
        root.bind("<Control-c>", cancel)

        def confirm(e):
            fin([i.to_dict() for i in widget.tree.get_checked()])

        widget.confirm_button.bind("<Button-1>", confirm)
        widget.confirm_button.bind("<Return>", confirm)
        widget.confirm_button.bind("<space>", confirm)
        root.bind("<Control-Return>", confirm)

        if at_focus_out:
            if at_focus_out == "confirm":
                root.bind("<FocusOut>", lambda e: (confirm(None) if e.widget == root else None))
            else:
                root.bind("<FocusOut>", lambda e: (cancel(None) if e.widget == root else None))

        if return_mode == "value at action":

            def single_return(e):
                if c := widget.tree.get_checked():
                    fin([i.to_dict() for i in c])
                else:
                    fin(None)

            widget.tree.bind("<Return>", single_return, add=True)
            widget.tree.bind("<space>", single_return, add=True)
            widget.tree.bind("<Button-1>", single_return, add=True)
            widget.tree.bind("<Double-Button-1>", single_return, add=True)
            widget.tree.bind("#", single_return, add=True)

        # (Trial-and-Error knowledge)
        # The styling must be defined here and then <.update_idletasks> executed.
        # [ see also <treeselect.SelectTreeWidget.__init__> ]
        # If the styling is defined in the <SelectTreeWidget>,
        # it is not applied to the <SelectTreeWidget.SelectTree(ttk.Treeview)>.
        # Not even if <.update_idletasks> is executed in <SelectTreeWidget> 
        # or <.update_idletasks> is executed here after the constructor of <SelectTreeWidget>.
        # The styling for <SelectTreeWidget.SelectTree(ttk.Treeview)> is also not applied
        # if <.update_idletasks> is executed after the return of the main Tk object from this function.
        # [ see <server.__call__.wrapper.proc> ]
        if default_styling:
            style = ttk.Style()

            style.configure(
                "Treeview",
                weight="normal",
                size=10
            )
            font = tkFont.Font()
            font.configure(underline=True, weight="bold", size=10)
            style.map('Treeview', font=[('selected', font)], background=[], foreground=[('selected', '#000000')])

            style.map(
                "expand.TButton",
                foreground=[('active', 'blue')],
                background=[('active', '#FFFFFF')],
                relief=[('active', 'flat')],
            )
            style.configure(
                "expand.TButton",
                weight="normal", size=10,
                background="#FFFFFF",
                foreground="#000000",
                relief="flat"
            )
            widget.expand_button.configure(style="expand.TButton")

            style.map(
                "cancel.TButton",
                foreground=[('active', 'red')],
                background=[('active', '#FFFFFF')],
                relief=[('active', 'flat')],
            )
            style.configure(
                "cancel.TButton",
                weight="normal", size=10,
                background="#FFFFFF",
                foreground="#000000",
                relief="flat"
            )
            widget.cancel_button.configure(style="cancel.TButton")

            style.map(
                "confirm.TButton",
                foreground=[('active', 'blue')],
                background=[('active', '#FFFFFF')],
                relief=[('active', 'flat')],
            )
            style.configure(
                "confirm.TButton",
                weight="normal", size=10,
                background="#FFFFFF",
                foreground="#000000",
                relief="flat"
            )
            widget.confirm_button.configure(style="confirm.TButton")

        root.update_idletasks()

        return root

    return func()


if __name__ == '__main__':
    structure = (
        StructureNode("L0", "V0",
                      StructureNode("L0-0", "V0-0"),
                      StructureNode("L0-1", "V0-1"),
                      StructureNode("L0-2", "V0-2"),
                      ),
        StructureNode("L1", "V1"),
        StructureNode("L2", "V2",
                      StructureNode("L2-0", "V2-0",
                                    StructureNode("L2-0-0", "V2-0-0"),
                                    StructureNode("L2-0-1", "V2-0-1"),
                                    StructureNode("L2-0-2", "V2-0-2"),
                                    ),
                      StructureNode("L2-1", "V2-1"),
                      ),
    )
    data = server = popup(*structure)
    print(data)
