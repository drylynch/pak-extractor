from pathlib import Path
import pakstuff
import argparse
import os

DEFAULT_OUTPUT_DIR = 'compiled/'


def compile_pak(original_pak_path, input_files_dir, output_dir):
    """ compiles a .pak from files. needs original .pak, input files as describes in its table of contents, and optional output dir.
        writes to '[output dir]/[input pak name].pak' """
    original_pak_path = Path(original_pak_path)  # all paths are Path objs
    input_files_dir = Path(input_files_dir)
    output_pak_path = Path(output_dir) / original_pak_path.name
    outpak = pakstuff.Pak()

    print("compiling '{0}' ... ".format(output_pak_path), end='')

    # get stuff from the original .pak file
    with open(original_pak_path, 'rb') as f:
        pakstuff.validate_magic_number(f)
        outpak.mystery_id = pakstuff.read_mystery_id_from_pak(f)
        outpak.table_of_contents = pakstuff.read_toc_from_pak(f)

    # import all data into their respective PakFiles in table of contents
    cursor = pakstuff.OFFSET_DATA_START  # intial offset, after header
    for t in outpak.table_of_contents:
        filepath = input_files_dir / t.path
        with open(filepath, 'rb') as f:
            t.set_data(f.read())
        t.data_offset = cursor
        cursor = t.data_offset + t.data_length + t.data_padding_length  # update cursor position to the byte after this data block
    outpak.toc_offset = cursor  # table of contents comes after all data blocks

    # write
    outpak.compile_to(output_pak_path)
    print('done.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-out', action="store", default=DEFAULT_OUTPUT_DIR, help="custom output directory, (default '{0}')".format(DEFAULT_OUTPUT_DIR))
    parser.add_argument('path_pak', help='path to .pak file / directory of .pak files to compile')
    parser.add_argument('path_files', help='path to directory of files needed to compile .pak')
    args = parser.parse_args()

    args.path_pak = Path(args.path_pak)
    args.path_files = Path(args.path_files)
    args.out = Path(args.out)

    if not args.path_pak.exists():
        print("ERROR: file/folder '{0}' not found!".format(args.path))
    elif args.path_pak.is_dir():  # compile all .paks in this dir
        for item in os.listdir(args.path_pak):
            filename = args.path_pak / Path(item)
            if filename.is_file() and filename.suffix == '.pak':  # only .pak files
                compile_pak(filename, args.path_files, args.out)
    else:  # path_pak is a .pak file, normal compile
        compile_pak(args.path_pak, args.path_files, args.out)
