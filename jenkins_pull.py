# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 11:43:55 2019

@author: dylan.melville
"""

import jenkins
import lxml
import requests
import pandas
import os
import datetime

def get_jobs_list():
    #List of jobs from Jenkins API
    # From site surveys. These all have the format
    # {Three letter location ID}{Count number}{"10S-"}{Three letter loc}{SUR##}
    cbs_jenkins = jenkins.Jenkins('http://jenkins.bloodservices.ca')
    job_details_list = cbs_jenkins.get_job_info_regex('\w\w\w10S-\w\w\wSUR\d\d')
    
    return job_details_list
    

def get_potentially_null_property(job,args):
    #Returns the build number for a specific job build. If a list is empty,
    # the exception is handled and Null is returned.
    
    #Input: a job dictionary, and the arguements for dictionaries and lists 
    # needed to find the number
    #Output: A value or a NULL if no builds of this type have been done
    obj = job
    for arg in args:
        try:
            obj = obj[arg]
        except IndexError:
            return None
        except TypeError:
            return None
    return obj
    
def clean_jenkins_output(job_list):
    #Input: list of dictionaries, each containing one job details
    #Output: dictionary where each value is a list of entries corresponding to the key
    keys = ['description','name','url','buildable','color']
    key_value_tuples = [(key,[job[key] for job in job_list]) for key in keys]
    
    build_count_tuple = ('buildsCount',[get_potentially_null_property(job,['builds',0,'number']) for job in job_list])
    last_completed_tuple = ('lastCompletedBuildNum',[get_potentially_null_property(job,['lastCompletedBuild','number']) for job in job_list])
    last_successful_tuple = ('lastSuccessfulBuildNum',[get_potentially_null_property(job,['lastSuccessfulBuild','number']) for job in job_list])
    last_failed_tuple = ('lastFailedBuildNum',[get_potentially_null_property(job,['lastFailedBuild','number']) for job in job_list])
    last_stable_tuple = ('lastStableBuildNum',[get_potentially_null_property(job,['lastStableBuild','number']) for job in job_list])
    last_unsuccessful_tuple = ('lastUnsuccessfulBuildNum',[get_potentially_null_property(job,['lastUnsuccessfulBuild','number']) for job in job_list])
    health_report_description_tuple = ('healthReportDescription',[get_potentially_null_property(job,['healthReport',0,'description']) for job in job_list])
    health_report_score_tuple = ('healthReportScore',[get_potentially_null_property(job,['healthReport',0,'score']) for job in job_list])
    
    key_value_tuples.append(build_count_tuple)
    key_value_tuples.append(last_completed_tuple)
    key_value_tuples.append(last_successful_tuple)
    key_value_tuples.append(last_stable_tuple)
    key_value_tuples.append(last_failed_tuple)
    key_value_tuples.append(last_unsuccessful_tuple)
    key_value_tuples.append(health_report_description_tuple)
    key_value_tuples.append(health_report_score_tuple)
    
    return_dict = dict(key_value_tuples)
    return return_dict
    

def generate_dataframe_from_list(clean_jobs_list):
    #Take the list of jobs, and make a dictionary for each build in its own.
    # Each sublist should have:
    # [job_ID,URL,build_count,last_completed_build_url]
    df_job_list = clean_jenkins_output(clean_jobs_list)
    data_frame = pandas.DataFrame(df_job_list)
    return data_frame
    
    
def get_job_log(job_name):
    return

def full_process():
    TODAY = datetime.date.today()
    
    jl = get_jobs_list()
    clean_list = clean_jenkins_output(jl)
    data_frame = pandas.DataFrame(clean_list)
    user_profile = os.environ['USERPROFILE']
    filepath = user_profile + '\\logs\\Jenkins_job_'+ str(TODAY) +'.csv'
    export_csv = data_frame.to_csv(filepath, index = None, header=True) #Don't forget to add '.csv' at the end of the path
    
    return export_csv
if __name__ == '__main__':
    print('In MAIN')
    print(full_process())