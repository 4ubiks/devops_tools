# devops_tools
small tools i build to help automate processes and optimize workflow {insert buzzword here}

## `cpu.sh` (Linux)
a program to check cpu info. runtime, % usage, top 5 most intensive processes, and cpu summary (byte order, bitness, architecture, etc)

## `ldapConfig.sh`
When run on an Ubuntu Linux server, it joins the box to a specified domain. Then, joins a user to the domain, from the newly configured box.

## `mirrorReport.rb` (GitLab Rails console)
returns information about each mirrored repository that currently is not working properly. good for easy troubleshooting and informative investigation

## `getFiles.py` 
should be run on an Artifactory instance to return every *file* inside of your instance, and its direct parent directory. prompts you for a parent directory and a specific path, if you want to get an overview of a specific area of your Artifactory instance.

## `purgeFiles.py`
An extension of `getFiles.py`. This script will traverse every single object in an Artifactory instance, and if they are marked with a particular property and have a age (in days) larger than their property value, they will be deleted from the artifactory instance. Great for cleanup and expulsion of old, outdated files. 

## `weeklytask.py
A script that generates a template `.md` file to visualize my work week. Displays event hours and office hours that I fill in later. Meant to quickly generate the template with weekdates already inputted. Great for lazy people. 
