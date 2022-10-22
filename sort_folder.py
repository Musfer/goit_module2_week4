import shutil
from threading import Thread
from pathlib import Path
import argparse
import time
import sys
import os

parser = argparse.ArgumentParser(description="Sorting folder")
parser.add_argument("--source", "-s", help="Source folder", required=True)
args = vars(parser.parse_args())
source = args.get("source")

ignore_folders = []  # folders that should not be parsed
base_folder = Path("")
extension_found = set()
unknown_extensions = set()
file_logs = {
    "images": [], "video": [], "documents": [], "audio": [], "archives": []
}

known_extensions = {
    "JPEG": "images", "PNG": "images", "JPG": "images", "SVG": "images", "BMP": "images",
    "AVI": "video", "MP4": "video", "MOV": "video", "MKV": "video",
    "DOC": "documents", "DOCX": "documents", "TXT": "documents",
    "PDF": "documents", "XLSX": "documents", "PPTX": "documents",
    "MP3": "audio", "OGG": "audio", "WAV": "audio", "AMR": "audio",
    "ZIP": "archives", "TAR.GZ": "archives", "GZ": "archives", "TAR": "archives",
    "TAR.XZ": "archives", "TAR.BZ": "archives"
}


CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ"
TRANSLATION = ("a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
               "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya", "je", "i", "ji", "g")
TRANS = {}
for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION):
    TRANS[ord(c)] = l
    TRANS[ord(c.upper())] = l.upper()


def normalize(name):
    newname = []
    for i in name:
        if i.isalpha() or i.isdigit():
            newname.append(i)
        else:
            newname.append("_")
    return ("".join(newname)).translate(TRANS)


def folder_content(path: Path):
    folders = []
    files = []
    for el in path.iterdir():
        if el.is_dir():
            folders.append(el)
        if el.is_file():
            files.append(el)
    return folders, files


def deal_with_file(path: Path):
    head, tail = os.path.split(path)
    name_lst = tail.split(".")
    ext = ""
    for i in range(len(name_lst)):
        guess_ext = ".".join(name_lst[i:])
        if guess_ext.upper() in known_extensions.keys():
            ext = guess_ext.upper()
            break
    if ext == "":
        if len(name_lst) > 0:
            unknown_extensions.add(".".join(name_lst[1:]))
    else:
        extension_found.add(ext)

    name = ".".join(name_lst[:len(name_lst)-len(ext)])
    target_type_folder = known_extensions.get(ext, None)  # where to move the file
    if target_type_folder:
        target_folder_path = base_folder / target_type_folder
    else:
        return None
    while True:
        try:
            prefix = 1
            while True:
                if target_type_folder == "archives":
                    file_name = f"{name}_{prefix}"
                else:
                    file_name = f"{name}_{prefix}.{ext}"
                if (target_folder_path / file_name).exists():
                    prefix += 1
                else:
                    break
            target_path = target_folder_path / file_name

            if target_type_folder == "archives":
                pass
                os.mkdir(target_path)
                shutil.unpack_archive(path, target_path)
                os.remove(path)
                file_logs.get(target_type_folder).append(f"'{path}' \t UNPUCKED TO \t '{target_path}'")
            else:
                shutil.move(path, target_path)
                file_logs.get(target_type_folder).append(f"'{path}' \t MOVED TO \t '{target_path}'")
            break
        except FileExistsError:
            pass


def deal_with_folder(path: Path):
    folders, files = folder_content(path)
    threads = []
    for folder in folders:
        if folder in ignore_folders:
            continue
        th = Thread(target=deal_with_folder, args=(folder,))
        th.start()
        threads.append(th)
    for file in files:
        deal_with_file(file)
    [th.join() for th in threads]
    if not os.listdir(path):
        try:
            os.rmdir(path)
        except OSError:
            pass


def create_type_folders(path: Path):
    for type_of_files in set(known_extensions.values()):  # create folders like "images" if they do not exist
        new_folder_path = path / type_of_files
        ignore_folders.append(new_folder_path)
        try:
            new_folder_path.mkdir(exist_ok=True)
        except OSError:
            pass


if __name__ == '__main__':
    base_folder = Path(source)
    if not base_folder.is_dir():
        print(f"{base_folder} does not exist")
        sys.exit()
    try:
        create_type_folders(base_folder)
        deal_with_folder(base_folder)
    except Exception as err:
        print(err)
    with open(base_folder.joinpath("logs.txt"), "w", encoding="utf-8") as logs:  # printing logs
        print(f"Extentions found: {', '.join(extension_found)}", file=logs)
        print(f"Unknown extensions: {', '.join(unknown_extensions)}", file=logs)

        print("Files sorted:", file=logs)
        for files in file_logs.keys():
            print(f"\t{files}: ", file=logs)
            for i in file_logs[files]:
                print("\t\t" + i, file=logs)
    print(f"See logs in '{base_folder.joinpath('logs.txt')}'")

    #                                 testing
    # n = 1
    # total_time = 0
    # for i in range(n):
    #     print(i)
    #
    #     shutil.rmtree("Trashfolder2")
    #     shutil.copytree("Trashfolder", "Trashfolder2")
    #     base_folder = Path("Trashfolder2")
    #
    #     if not base_folder.is_dir():
    #         print(f"{base_folder} is not a folder")
    #         sys.exit()
    #     start = time.perf_counter()
    #     create_type_folders(base_folder)
    #     deal_with_folder(base_folder)
    #     with open(base_folder.joinpath("logs.txt"), "w", encoding="utf-8") as logs:  # printing logs
    #         print(f"Extentions found: {', '.join(extension_found)}", file=logs)
    #         print(f"Unknown extensions: {', '.join(unknown_extensions)}", file=logs)
    #
    #         print("Files sorted:", file=logs)
    #         for files in file_logs.keys():
    #             print(f"\t{files}: ", file=logs)
    #             for i in file_logs[files]:
    #                 print("\t\t" + i, file=logs)
    #     print(f"See logs in '{base_folder.joinpath('logs.txt')}'")
    #     end = time.perf_counter()
    #     print(end - start)
    #     total_time += (end - start)/ n
    # print(total_time)
