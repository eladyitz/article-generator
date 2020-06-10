import os
import re
import shutil


def _warning(msg):
    print("WARNING: " + msg)


def _dump_file(output_f, include_file):
    with open(include_file, encoding='utf8') as f:
        for line in f:
            output_f.write(line)


def _consolidate_paper(tex_dir, tex_files, main='main.tex'):
    print("consolidate folder {} with {} files, main is {}".format(tex_dir, tex_files, main))

    r = re.compile(r'\\(include|input)\s+(\S+)')
    dst = "{}.tex".format(tex_dir)

    with open(dst, 'w', encoding='utf8') as output_f:
        with open(os.path.join(tex_dir, main), encoding='utf8') as input_f:
            for line in input_f:
                if r.match(line):
                    included = r.match(line).group(2) + '.tex'
                    # note: currently we assume no recursive includes, we'd check later if it's needed adding
                    if included in tex_files:
                        _dump_file(output_f, os.path.join(tex_dir, included))
                else:
                    output_f.write(line)

    print("folder {} consolidated".format(tex_dir, tex_files, main))
    file_content = open(output_f.name, "r", encoding='utf8').read()
    return file_content


def _search_main_tex(tex_dir, tex_files):
    r = re.compile(r'^\s*\\documentclass')
    for tex_file in tex_files:
        filename = os.path.join(tex_dir, tex_file)
        with open(filename, encoding='utf8') as f:
            try:
                for line in f:
                    if r.match(line):
                        return tex_file
            except UnicodeDecodeError:
                _warning("Decoding error in: " + filename)
    return None


def consolidate_papers(tex_files, tex_dir):
    if len(tex_files) == 1:
        print("foldr {} has only one file {}".format(tex_dir, tex_files[0]))
        try:
            shutil.copyfile(os.path.join(tex_dir, tex_files[0]), "{}.tex".format(tex_dir))
            return open(os.path.join(tex_dir, tex_files[0]), "r", encoding='utf8').read()
        except UnicodeDecodeError:
            _warning("Decoding error in: " + os.path.join(tex_dir, tex_files[0]))
            return ""

    elif 'main.tex' not in tex_files:
        main = _search_main_tex(tex_dir, tex_files)
        if main is None:
            _warning("directory {} is without main.tex file".format(tex_dir))
        else:
            consolidated_paper = _consolidate_paper(tex_dir, tex_files, main)
    else:
        consolidated_paper = _consolidate_paper(tex_dir, tex_files)

    return consolidated_paper
