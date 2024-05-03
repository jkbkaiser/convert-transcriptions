import argparse
import csv
import re
from argparse import Namespace
from io import TextIOWrapper
from pathlib import Path
from typing import Union, cast

from constants import *


class Reader:
    def __init__(self, file: TextIOWrapper):
        self.file = file
        self.curr_line = file.readline().strip()
        self.next_line = file.readline().strip()
        self.curr_line_number = 1
        self.next_line_number = 2

    def __next__(self) -> bool:
        self.curr_line = self.next_line
        self.curr_line_number = self.next_line_number

        # Skip lines that start with whitespace
        # In the future this might need to be done better
        if not self.file.readable():
            return False

        new_line = self.file.readline()
        self.next_line_number += 1
        while not new_line or new_line[0].isspace() or new_line[0] == "%":
            if not new_line or not self.file.readable():
                return False

            new_line = self.file.readline()
            self.next_line_number += 1

        self.next_line = new_line.strip()
        return True

    def get_line_number(self) -> int:
        return self.curr_line_number

    def get_line(self) -> str:
        return self.curr_line

    def peek_line(self) -> str:
        return self.next_line


def parse_line(line: str) -> dict[str, str]:
    m = re.search(
        rf"^\*(?P<{SPEAKER_COL}>.+):\s*(?:\[-\s[a-zA-Z]+])*(?P<{SENTENCE_COL}>.*)$",
        line,
    )
    if m is None:
        raise Exception(f"Could not parse line: {line}")
    return m.groupdict()


def number_of_switches(line: str) -> int:
    m = re.findall(r"(int@x|@s)", line)
    return len(m)


def is_segment_header(line: str) -> bool:
    return line.startswith(SEGMENT_PREFIX)


def is_end(line: str) -> bool:
    return line.startswith(END_HEADER)


def get_subject_id(filename: str) -> int:
    m = re.search(r"^(\d+)_\d+.cha$", filename)
    if m is None:
        raise Exception("Syntax error: Could not parse file name: {}", filename)
    return int(m.groups()[0])


def get_segment_number(line: str) -> int:
    m = re.search(r"^@T:\s*(\d+).*$", line)
    if m is None:
        raise Exception("Syntax error: Could not parse segment number: {}", line)
    return int(m.groups()[0])


def parse_segments(subject_id: int, reader: Reader) -> list[dict[str, Union[str, int]]]:
    rows = []

    while next(reader):
        curr_line = reader.get_line()
        if not is_segment_header(curr_line):
            raise Exception(
                f"Syntax error: Could not parse segment header: {curr_line}"
            )
        segment_number = get_segment_number(curr_line)

        while (
            not is_segment_header(reader.peek_line())
            and next(reader)
            and not is_end(reader.get_line())
        ):
            curr_line = reader.get_line()
            num_switches = number_of_switches(curr_line)

            if num_switches > 0:
                parsed_line = parse_line(curr_line)
                row = cast(dict[str, Union[str, int]], parsed_line)
                row[SUBJECT_ID_COL] = subject_id
                row[SEGMENT_ID_COL] = segment_number
                row[ROW_NUMBER_COL] = reader.get_line_number()
                row[SWITCH_COUNT] = num_switches

                for _ in range(num_switches):
                    rows.append(row)

    return rows


def is_header(line: str, headers: list[str]) -> bool:
    # TODO: this might not always be the case, needs to be verified
    if line[0] == "*":
        return False

    for header in headers:
        if line.startswith(header):
            return True

    return False


def skip_headers(reader: Reader, headers: list[str]):
    while is_header(reader.peek_line(), headers):
        next(reader)


def skip_all_headers(reader: Reader):
    skip_headers(reader, HIDDEN_HEADERS)
    skip_headers(reader, INITIAL_HEADERS)
    skip_headers(reader, PARTICIPANT_SPECIFIC_HEADERS)
    skip_headers(reader, CONSTANT_HEADERS)
    skip_headers(reader, CHANGABLE_HEADERS)


def process_file(filepath: Path) -> list[dict[str, Union[str, int]]]:
    with filepath.open("r") as f:
        reader = Reader(f)
        subject_id = get_subject_id(filepath.name)
        skip_all_headers(reader)
        segments = parse_segments(subject_id, reader)

    return segments


def write_to_file(output_filepath: Path, rows: list[dict[str, Union[str, int]]]):
    with open(output_filepath, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=TABLE_COLS, delimiter=",")
        writer.writeheader()
        writer.writerows(rows)


def run(args: Namespace):
    source_path = Path(args.sources)
    output_filepath = Path(args.output_filename)

    rows = []

    for filepath in source_path.iterdir():
        if not filepath.name.endswith(".cha"):
            continue

        print(f"Processing: {filepath}")
        rows += process_file(filepath)

    write_to_file(output_filepath, rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Calm CHAT@CSV",
        description="This is a small script that can be used to automate some part of converting CHAT files to CSV files",
    )
    parser.add_argument(
        "--sources",
        "-s",
        default="./sources",
        type=str,
        help="provide a path to the source directory, all files that should be parsed should be placed here",
    )
    parser.add_argument(
        "--output-filename",
        "-o",
        default="./output/output.csv",
        type=str,
        help="provide a path to the file to which the output should be written",
    )
    args = parser.parse_args()
    run(args)
