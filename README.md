# Description
This program converts `.cha` files to a csv format. This code was developed using
python version 3.11.4, but should work in 3.8+. No libraries were used outside the
standard library, so everything should work out of the box. For more details on
how to install python, take a look [here](https://www.python.org/).

To use this program, first clone the project using

`git clone git@github.com:jkbkaiser/convert_transcriptions.git`

or download and extract the raw files. Next, place all files that need be
processed in the `sources` directory/folder. From the root of the project run
the command

`python main.py`

to process the documents. The resulting csv file is written to `output/output.csv` by
default.
