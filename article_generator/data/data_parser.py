import os
import shutil
import subprocess
import re


def _get_main_tex_file(tex_dir, tex_files):
    r = re.compile(r'^\s*\\documentclass')
    for tex_file in tex_files:
        filename = os.path.join(tex_dir, tex_file)
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                for line in f:
                    if r.match(line):
                        return tex_file
            except UnicodeDecodeError as exc:
                print("Decoding error in: {}, reason: {}".format(filename, exc))
                return None
    return None


def consolidate_papers(paper):
    tex_files = [file for file in os.listdir(paper['paper_full_path']) if file.endswith(".tex")]
    new_paper_file_name = "{}.txt".format(paper['paper_file_name'])
    consolidated_paper = os.path.join("..", paper['paper_folder_label'], new_paper_file_name)

    if "main.tex" in tex_files:
        main_tex = "main.tex"
    elif len(tex_files) == 1:
        main_tex = tex_files[0]
    else:
        main_tex = _get_main_tex_file(paper['paper_full_path'], tex_files)
        if not main_tex:
            print("there is no main.tex and there is more than 1 file in folder: {}".format(paper['paper_full_path']))
            return None

    current_path = os.getcwd()
    os.chdir(paper['paper_full_path'])
    subprocess.run("detex {} > {}".format(main_tex, consolidated_paper),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            check=True,
                            text=True,
                            shell=True)

    try:
        with open(consolidated_paper, "r+", encoding='utf-8') as paper_file:
            paper_content = paper_file.read()
            paper_content = re.sub(r'\n\s*\n', '\n\n', paper_content)
            paper_file.seek(0)
            paper_file.write(paper_content)
            paper_file.truncate()
    except UnicodeDecodeError as exc:
        print("Decoding error in: {}, reason: {}".format(consolidated_paper, exc))
        os.remove(consolidated_paper)
        paper_content = None

    try:
        os.chdir(current_path)
        shutil.rmtree(paper['paper_full_path'])
    except OSError as exc:
        print("Cant delete dir {}, {}".format(paper['paper_full_path'], exc))

    paper['paper_file_name'] = new_paper_file_name
    paper['paper_full_path'] = os.path.join(paper['paper_prefix_path'], new_paper_file_name)

    return paper_content
