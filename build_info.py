# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 09:14:33 2019

@author: dylan.melville
"""

from bs4 import BeautifulSoup
import re
import requests
import pandas
import os
import tkinter
import tkinter.filedialog
import datetime

def load_job_details(today_log = True):
    #Gets the data from recent jobs API pull. Takes today's API pull if available
    if (today_log):
        TODAY = datetime.date.today()
        file_name = '\logs\Jenkins_jobs_' + str(TODAY) + '.csv'
        file_path = os.getcwd()+file_name if os.path.isfile(os.getcwd() + file_name) else input_file()
    else:
        file_path = input_file()
    job_details = pandas.read_csv(file_path)
    
    return job_details

def generate_builds_dataframe(jobs):
    #Takes a list of Job objects, and creates a dataframe containing all the build data
    # from those jobs
    #Input: List of Jobs
    #Output: Dataframe which takes its columns from the successful build which
    # has the most columns among the jobs.
    # Externality: Creates a csv log of the build data
    
    #Make a list of builds
    builds_1d = [item for sublist in jobs for item in jobs[sublist].builds]
    #Determine the build with the most details as default. Add null details to
    # builds with less.
    details_lengths = [(len(build.details),build) for build in builds_1d]        
    most_details_build = max(details_lengths)
    dataframe_columns = most_details_build[1].details.keys()
    #Any builds that don't have a column for whatever reason will be added with NULL
    data = dict(zip(dataframe_columns,[[] for col in dataframe_columns]))
    for build in builds_1d:
        diff = dataframe_columns - build.details.keys()
        for col in diff:
            build.details[col] = "NULL"
        #Add build to dict
        [data[col].append(build.details[col]) for col in build.details]
    #Now we have a dictionary for the dataframe
    builds_df = pandas.DataFrame.from_dict(data)
    builds_df.to_csv(os.getcwd() + '\logs\Jenkins_builds_' + str(datetime.date.today()) + '.csv')
    return builds_df

def generate_jobs_from_dataframe(jobs_dataframe):
    #Takes a dataframe containing job details, and outputs a dictionary of 
    # (key) job names and (value) Job objects.
    #Input: Dataframe from the output of the jenkins_pull.py csv output.
    #Output: Dictionary which has job names as the key and Job objects as the
    # values
    length = len(jobs_dataframe.index)
    jobs_list = [(jobs_dataframe.iloc[iloc_index]['name'],Job(jobs_dataframe.iloc[iloc_index])) for iloc_index in range(length)]
    jobs_dict = dict(jobs_list)
    return jobs_dict
    
def input_file():
    #Gets the csv file with all the up to date Jenkins Job details
    #Input: Path of selected file.
    #Output: String with the selected file_path
    root = tkinter.Tk()
    root.withdraw()
    file_path = tkinter.filedialog.askopenfilename()
    
    return file_path
    
class Build:
    #Object for a single build of a site survey. Details include job information
    # And details scraped from the full console output as pulled from a Jenkins
    # http request.
    def __init__(self, job, number):
        self.job_name = job.name
        self.number = number
        self.url = job.url+str(number)+'/'
        self.log_url = self.url+'consoleFull'
        self.full_log = self.get_log()
        self.build_result = self.get_build_result()
        self.details = self.scrape_log()
        
    def __gt__(self,other):
        #This is for comparison using (max) for outputting the dataframe.
        # Comparison isn't really important, but there needs to be something
        # in place to use max() on a tuple involving Build objects
        return self.number > other.number
    
    def __lt__(self,other):
        #This is for comparison using (max) for outputting the dataframe.
        # Comparison isn't really important, but there needs to be something
        # in place to use max() on a tuple involving Build objects
        return self.number < other.number
    
    def get_build_result(self):
        #Gets the overall result of the build. This is either SUCCESS or FAILURE
        # depending on criteria on the ping, jitter, upload and download speed.
        # Always the last 8 characters of the console output
        #Input: self
        #Output: 8 character string, which is the build result
        return self.full_log[-8:-1]

    def get_log(self):
        #Gets the full console output using url and an http request
        #Input: self
        #Output: String containing the full console output. Lines separated with \n
        web_request = requests.get(self.log_url)
        full_HTML = web_request.text
        soup = BeautifulSoup(full_HTML, "html.parser")
        #The pages only have one <pre> tag on them, so just grab the first found
        full_log = soup.find_all("pre")[0].text
        return full_log
    
    def scrape_log(self):
        #Scrapes key details from the console output from Jenkins. This includes
        # the feilds from the Test Summary Result table, which includes location
        # information and the Ping, Jitter, Upload, and Download. Also, the contents
        # from the device information (labelled "Carrier Info" in the console)
        #Input: self
        #Output: dictionary containing all the scraped details

        tsr_fields = ['Site Code','Site Key','Clinic Name','Address','City','Province','Postal Code','Position in Clinic','Carrier','Ping','Download','Upload','Jitter']
        tsr_regex = [self.get_test_summary_result(label) for label in tsr_fields]
        tsr_tuples = zip(tsr_fields,tsr_regex)
        tsr_info = dict(tsr_tuples)
        #Get the carrier info from carrier info dictionary:
        carrier_info = self.get_carrier_info()
        #Get if the build finished as a success or failure
        result_info = dict([('result',self.full_log[-8:-1])])
        #These are the details stored in the object from the job
        job_fields = ["job_name","build_number","URL"]
        job_values = [self.job_name, str(self.number), self.url]
        job_info = dict(zip(job_fields,job_values))
        
        full_details = dict(job_info,**tsr_info,**carrier_info,**result_info)
        return full_details
    
    def get_carrier_info(self):
        #Get the information from the dictionary labelled "Carrier Info".
        # This includes the carrier, device info, SIM card number etc.
        #Input: self
        #Output: dictionary containing all the info from the Carrier Info
        # string in the console
        
        #first, get the dictionary from the log output using a regex for the 
        # first entry of the dictionary
        regex_string = '{"ipAddr.*}'
        regex_result = re.search(regex_string,self.full_log)
        if (type(regex_result) == type(None)):
            fields = ["ipAddr","rssi","network","imei","imsi","serviceType","simCardNumber","apn","phoneNumber","coreTemperature","activityStatus","rsrp","rsrq","recordTime"]
            blank_values = ["NULL" for i in range(len(fields))]
            return dict(zip(fields,blank_values))
        #This returns as a string surrounded by curly brackets, so we'll peel
        # those off and split it into a list of tuples
        string_dict = regex_result.group(0)[1:-1]
        st_split = string_dict.split(',')
        tuples_list = [group[1:-1].split('":"') for group in st_split]
        info = dict(tuples_list)
        #Since excel truncates integers greater than 16 digits, we add
        # quotations to the 21 digit sim card numbers.
        info['simCardNumber'] = '"'+str(info['simCardNumber'])+'"'
        info['imei'] = '"'+str(info['imei'])+'"'
        info['imsi'] = '"'+str(info['imsi'])+'"'
        return info    
    
    def get_test_summary_result(self,info_key):
        #This function is string processing on the data from the log that 
        # is organized in the TEST SUMMARY RESULTS table in the Jenkins log.
        #Input: The label in the test summary results field for the data
        # desired
        #Output: The value in the table.
        regex_string = '(/// '+info_key+': *)(.*)'
        match = re.search(regex_string, self.full_log)
        if (match):
            content = match.group(2)[:-1]
            return content
        else:
            return "NULL"
        

class Job:
    def __init__(self, job_dictionary):
        self.name = job_dictionary['name']
        self.build_count =int(job_dictionary['buildsCount'])
        self.url = job_dictionary['url']
        self.health_report = {'Description':job_dictionary['healthReportDescription'],'Score':job_dictionary['healthReportScore']}
        self.builds = self.generate_builds()
        self.key_build_nums = [job_dictionary['lastSuccessfulBuildNum'],job_dictionary['lastStableBuildNum'],job_dictionary['lastUnsuccessfulBuildNum'],job_dictionary['lastFailedBuildNum'],job_dictionary['lastCompletedBuildNum']]
        self.key_builds = self.label_key_builds(job_dictionary['lastSuccessfulBuildNum'],job_dictionary['lastStableBuildNum'],job_dictionary['lastUnsuccessfulBuildNum'],job_dictionary['lastFailedBuildNum'],job_dictionary['lastCompletedBuildNum'])

    def generate_builds(self):
        #Generate a list of builds of this survey key
        #Input: self
        #Output: list of builds for this job
        
        builds = [Build(self, int(num)) for num in range(1,self.build_count+1)]
        return builds
    
    def label_key_builds(self,last_successful,last_stable,last_unsuccessful,last_failed,last_complete):
        #Create a separate dictionary which references the key builds for the
        # job. These are all the most recent successful build, failed build etc.
        #Input: Self
        #Output: dictionary of key builds as labelled on Jenkins
        
        KEYS = ['Successful','Stable','Unsuccessful','Failed','Completed']
        key_nums = [int(num) for num in [last_successful,last_stable,last_unsuccessful,last_failed,last_complete]]
        build_objects = [(self.builds[index-1] if index != 0 else None) for index in key_nums]
        tuples_list = zip(KEYS,build_objects)
        return dict(tuples_list)
        
        
if __name__ == '__main__':
    print('In MAIN')
    #import jenkins_pull
    print('Running API pull')
    #jenkins_pull.full_process()
    print('generating dataframe')
    jobs_df = load_job_details()
    print('Building objects')
    job_objects = generate_jobs_from_dataframe(jobs_df)
    print('Making Builds Dataframe')
    builds_df = generate_builds_dataframe(job_objects)
    
    