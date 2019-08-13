# CMDC_Jenkins

This is a project that runs a data pull from the Jenkins API to get the network information gathered during speed tests.

## Getting Started

To use this you need:
- Python 3.6, best installed using [Anacoda](https://www.anaconda.com/distribution/#download-section)

You must have the following packages. Install missing packages with 'pip' or 'conda'
- Jenkins
- re
- bs4
- pandas
- os
- datetime
- tkinter
- requests

## Usage

To run the program, navigate to the location of the repository in command prompt.
Then, run the command `python jenkins_pull.py`.
Then, run the command `python build_info.py`

In a folder called logs at the current directory, two new csv files will have been made:
**Jenkins_jobs_DATE.csv** and **Jenkins_builds_DATE.csv**

These contain, first the information available about all the jobs for internet speed tests. The second has all the information about the builds of those jobs.
