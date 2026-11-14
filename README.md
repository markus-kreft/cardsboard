# Cardsboard

Terminal Kanban board for cards-based project management.

![Screen recording of cardsboard demo.](https://raw.githubusercontent.com/markus-kreft/cardsboard/main/docs/cardsboard.gif)


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
| ?                   | show shortcuts        |
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
| esc                 | abort input           |

## Configuration

If non-existent, Cardsboard creates a default configuration at `~/.config/cardsboard/config.ini`.
By default, items are opened in `$VISUAL` or `$EDITOR` (falling back to `vi`) in the same terminal. Cardsboard returns once the editor is closed.

To use a different program instead, set `cmd` to a command that can open Markdown files.
Use the placeholder `{}` for the absolute path to the file.

For example, to open files in vim in a Tmux popup you can use:
```ini
cmd = tmux popup -E vim "{}"
```

Or, to open files in vim in a new Alacritty terminal window:
```ini
cmd = alacritty --title cardsboard-popup -e bash -c 'vim "{}"' > /dev/null
```
Additional options like `--title` can tell the window manager to treat the window in a special way, e.g., as a pop-up window.

## Development

Cardsboard is developed with [uv](https://docs.astral.sh/uv/). Run the working tree directly with:

```sh
uv run cardsboard
```

Linting and type checking:

```sh
uv run ruff check
uv run ruff format --check
uv run ty check
```

## Similar Projects

- https://github.com/PlankCipher/kabmat
- https://github.com/smallhadroncollider/taskell
- https://github.com/arakkkkk/kanban.nvim
- https://warmedal.se/~bjorn/posts/vim-kanban-board.html
