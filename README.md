# Cardsboard

Terminal Kanban board for cards-based project management.

![Screen recording of cardsboard demo.](https://raw.githubusercontent.com/markus-kreft/cardsboard/5932105d3e44cb742075fcba2ec3bb0aeed1494c/docs/cardsboard.gif)


Under the hood Cardsboard functions as a file explorer.
Items are stored as simple files directly on the file system.
This means they can be easily edited by opening them in your preferred text editor.
Furthermore, this allows for easy synchronization and integration with scripting and automation.

The UI is inspired by simplifying the interface of Nextcloud Deck, removing all advanced features (collaboration, comments etc.).
Only the indicator of content in cards is kept, which allows to discern simple tasks from longer notes.

## Installation

```sh
pip install cardsboard
```

## Usage

`cardsboard [-h] [-d DATADIR]`

| Key                 | Description           |
|---------------------|-----------------------|
| q, ctrl + c         | quit                  |
| arrow left          | focus left            |
| arrow right         | focus right           |
| arrow up            | focus up              |
| arrow down          | focus down            |
| g                   | focus top item        |
| G                   | focus bottom item     |
| home                | focus first column    |
| end                 | focus last column     |
| Shift + arrow left  | move item left        |
| Shift + arrow right | move item right       |
| Shift + arrow up    | move item up          |
| Shift + arrow down  | move item down        |
| enter               | open focused item     |
| r                   | reload data from disk |
| o                   | insert item below     |
| i                   | rename focused item   |
| dd                  | delete focused item   |
| c                   | insert column right   |
| I                   | rename focused column |
| h                   | move column left      |
| l                   | move column right     |
| dc                  | delete column         |

## Configuration

If non-existent, Cardsboard creates a default configuration at `~/.config/keepmenu/config.ini`.
To be able to open and edit items you additionally need to set `cmd` to a program that can open Markdown files.
Use the placeholder `{}` for the absolute path to the file.

For example, to open files in vim in a new Alacritty terminal window you can use:
```ini
cmd = alacritty --title cardsboard-popup -e bash -c 'vim "{}"' > /dev/null`
```
Additional options like `--tilte` can tell the window manager to treat the window in a special way, e.g., as a pop-up window.

Furthermore, Cardsboard automatically detects when it is running inside Tmux and you can configure a special command for that case, e.g. use:
```ini
cmd_tmux = tmux popup -E vim "{}"
```

## Similar Projects

- https://github.com/PlankCipher/kabmat
- https://github.com/smallhadroncollider/taskell
- https://github.com/arakkkkk/kanban.nvim
- https://warmedal.se/~bjorn/posts/vim-kanban-board.html
