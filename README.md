
# \[Topic\] Tkinter Treeview styling in the background process

Platform specification:

- Pop!_OS 22.04 LTS
- Python 3.10.12 (main, Nov 20 2023, 15:14:05) [GCC 11.4.0] on linux
- `tk.TclVersion` == `tk.TkVersion` == 8.6
- `echo 'puts [info patchlevel];exit 0' | tclsh` == 8.6.12

Hello Community,

I have created a Tk interface for a superordinate project that should function as an 
independent popup like those in the `tk.filedialog` module.
Since this is to be completely deleted after the input query and this leads to

1. internal errors in Tk;
2. problems when calling the interface again

and the proposed solution of using `tk.Toplevel` did not produce the desired result, 
I decided to use a wrapper that executes the interface in an independent process in 
the background. The values are retrieved from the main process via a socket.

So after this issue was resolved, some other weird behavior occurred regarding the styling 
of `ttk.treeview`. With more trial-and-error than I would have liked, a satisfactory 
result was nevertheless achieved.

## The Issue

Although the tk objects are all created in the same process, 
it seems to matter where the styling is defined.

```
<Main process>
|	<Popup process>
|	|	root = make() {
|	|		root = tk.Tk()
|	|		widget = Widget(root) {
|	|			...
|	|			[3]
|	|		}
|	|		...
|	|		[2]
|	|		return root
|	|	}
|	|	[1]
|	|	root.mainloop()
|
|<Popup process>.start()
```

The styling of `ttk.Treeview` is only fully applied when the styling code is 
defined/executed at position `[2]` and then (before the return) `root.update_idletasks()` 
is executed.

However, if the styling code is defined/executed at position `[3]` or 
`root.update_idletasks()` is only executed after the return at position `[1]`, 
the parameter `font=[('selected', font)]` is not applied.

Asked on [Stackoverflow](...).

The entire code can be accessed on [Github](...).
