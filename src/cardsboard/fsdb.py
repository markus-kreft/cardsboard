import os
import shutil

from os.path import join, abspath
from os.path import basename as get_basename
from os.path import dirname as get_dirname


class fsDB:
    def __init__(self, basedir):
        self.basedir = basedir

    def _sorted_in_dir(self, dirname, reverse=False, dirs=False):
        # get only files or dirs
        dir_or_file = lambda f: f.is_dir() if dirs else f.is_file()
        get_key = lambda path: int(get_basename(path).split("_", 1)[0])
        list_to_sort = (abspath(f.path) for f in os.scandir(dirname) if dir_or_file(f))
        return sorted(list_to_sort, key=get_key, reverse=reverse)

    def parse(self):
        data = []
        for folder in self._sorted_in_dir(self.basedir, dirs=True):
            column = {}
            title = get_basename(folder).split("_", 1)[1]
            # column['path'] = folder
            column["title"] = title
            items = []
            for file in self._sorted_in_dir(folder):
                tag = None
                has_content = os.path.getsize(file) > 0
                if has_content:
                    with open(file) as f:
                        line = f.readline().strip()
                        if line.startswith("> tags:"):
                            tag = line[7:].strip()
                            line2 = f.readline()
                            if line2 == "":
                                has_content = False
                items.append(
                    {
                        "title": get_basename(file).split("_", 1)[1][:-3],
                        "has_content": has_content,
                        "tag": tag,
                    }
                )

            column["items"] = items
            data.append(column)
        self.data = data
        return data

    def get_path(self, col, row=None):
        """
        Get the file system path for a folder (given column only) or a file
        (given column and row).
        """
        if row is None:
            file = ""
        else:
            file = str(row) + "_" + self.data[col]["items"][row]["title"] + ".md"
        folder = str(col) + "_" + self.data[col]["title"]
        return join(self.basedir, folder, file)

    def swap(self, col, row, other_row):
        this_path_old = self.get_path(col, row)
        other_path_old = self.get_path(col, other_row)
        other_path_intermediate = join(self.basedir, "intermediate")

        # swap in the data
        self.data[col]["items"][row], self.data[col]["items"][other_row] = (
            self.data[col]["items"][other_row],
            self.data[col]["items"][row],
        )

        this_path_new = self.get_path(col, other_row)  # this item is now in other row
        other_path_new = self.get_path(col, row)

        os.rename(other_path_old, other_path_intermediate)
        os.rename(this_path_old, this_path_new)
        os.rename(other_path_intermediate, other_path_new)

    def insert_item_below(self, col, row, title):
        dirname = self.get_path(col)

        if len(self.data[col]["items"]) > 0:  # now there is at least one item
            new_row = row + 1
        else:
            new_row = 0
        new_prefix = str(new_row)

        for file in self._sorted_in_dir(dirname, reverse=True):
            prefix, basename = get_basename(file).split("_", 1)
            # break at insert point
            if int(prefix) == int(new_prefix) - 1:
                break
            # shift down file by one
            os.rename(file, join(dirname, str(int(prefix) + 1) + "_" + basename))

        # make new file
        path = join(dirname, new_prefix + "_" + title + ".md")
        open(path, mode="a").close()

        # insert in the data
        self.data[col]["items"].insert(
            new_row,
            {
                "title": title,
                "has_content": False,  # has to be empty because newly created
                "tag": None,
            },
        )

    def move_to_column(self, col, row, new_col):
        this_path_old = self.get_path(col, row)
        self.data[new_col]["items"].append(self.data[col]["items"][row])
        this_path_new = self.get_path(new_col, len(self.data[new_col]["items"]) - 1)
        os.rename(this_path_old, this_path_new)

        self.data[col]["items"].pop(row)
        self._excert(this_path_old)

    def rename_item(self, col, row, new_name):
        path_old = self.get_path(col, row)
        self.data[col]["items"][row]["title"] = new_name
        path_new = self.get_path(col, row)
        os.rename(path_old, path_new)

    def rename_column(self, col, new_name):
        path_old = self.get_path(col)
        self.data[col]["title"] = new_name
        path_new = self.get_path(col)
        os.rename(path_old, path_new)

    def insert_column_right(self, col, title):
        if len(self.data) > 0:  # now there is at least one column
            new_col = col + 1
        else:
            new_col = 0
        new_prefix = str(new_col)

        for folder in self._sorted_in_dir(self.basedir, dirs=True, reverse=True):
            prefix, basename = get_basename(folder).split("_", 1)
            # break at insert point
            if int(prefix) == int(new_prefix) - 1:
                break
            # shift down folder by one
            os.rename(folder, join(self.basedir, str(int(prefix) + 1) + "_" + basename))

        # make new file with new_basename
        path = join(self.basedir, new_prefix + "_" + title)
        os.mkdir(path)

        # insert in the data
        self.data.insert(
            new_col,
            {"title": title, "items": []},
        )

    def swap_column(self, col, other_col):
        this_path_old = self.get_path(col)
        other_path_old = self.get_path(other_col)
        other_path_intermediate = join(self.basedir, "intermediate")

        # swap in the data
        self.data[col], self.data[other_col] = self.data[other_col], self.data[col]

        this_path_new = self.get_path(other_col)  # this col is now in other col
        other_path_new = self.get_path(col)

        os.rename(other_path_old, other_path_intermediate)
        os.rename(this_path_old, this_path_new)
        os.rename(other_path_intermediate, other_path_new)

    def remove(self, col, row):
        path = self.get_path(col, row)
        self.data[col]["items"].pop(row)
        os.remove(path)
        self._excert(path)

    def remove_column(self, col):
        path = self.get_path(col)
        self.data.pop(col)
        shutil.rmtree(path)
        self._excert(path, isdir=True)

    def _excert(self, path, isdir=False):
        """
        Move files below the given path up one index. This assumes that the
        given path does not exist any more, i.e., has been deleted or moved.

        :param path: Path to the file that no longer exists.
        :param isdir: Whether the path is a directory
        :returns: None
        """
        if isdir:
            path = get_dirname(path)
        dirname = get_dirname(path)
        this_prefix, _ = get_basename(path).split("_", 1)
        # move up the ones below the exserted item
        for f in self._sorted_in_dir(dirname, dirs=isdir)[int(this_prefix) :]:
            prefix, basename = get_basename(f).split("_", 1)
            # shift up by one
            os.rename(f, join(dirname, str(int(prefix) - 1) + "_" + basename))
