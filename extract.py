from pathlib import Path
import pakstuff
import argparse
import os

DEFAULT_OUTPUT_DIR = Path('extracted/')


def extract_pak(input_pak, output_dir):
    """ extracts pak at path to output folder """
    input_pak = Path(input_pak)  # all paths are Path objs
    output_dir = Path(output_dir)
    with open(input_pak, 'rb') as f:
        pakstuff.validate_magic_number(f)
        print("extracting '{0}'... ".format(input_pak), end='')
        total_files_written = 0
        for t in pakstuff.read_toc_from_pak(f):  # extract each file from .pak
            output_path = output_dir / t.path
            f.seek(t.data_offset)
            data = f.read(t.data_length)
            output_path.parent.mkdir(parents=True, exist_ok=True)  # make sure output folder always exists
            output_path.write_bytes(data)  # write to file
            total_files_written += 1
        print('done. (wrote {0} files)'.format(total_files_written))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-out', action="store", default=DEFAULT_OUTPUT_DIR, help="custom output directory, (default '{0}')".format(DEFAULT_OUTPUT_DIR))
    parser.add_argument('path', help='path to .pak file or folder of .pak files to extract')
    args = parser.parse_args()

    args.path = Path(args.path)
    args.out = Path(args.out)
    if not args.path.exists():
        print("ERROR: file/folder '{0}' not found!".format(args.path))
    elif args.path.is_dir():  # extract all .paks in this dir
        for item in os.listdir(args.path):
            filename = args.path / Path(item)
            if filename.is_file() and filename.suffix == '.pak':  # only extract .pak files
                extract_pak(filename, args.out)
    else:  # path is a .pak file, normal extract
        extract_pak(args.path, args.out)
