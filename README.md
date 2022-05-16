# CWV
This script is supposed to perform a basic ETL job, using a mix of XML, text documents and API calls.

for every domain listed in domains.txt file ( homepage of a domain - f.ex. https://guzdek.co ):
1) find a robots.txt file
2) locate all sitemaps within robots.txt ( only website sitemaps, image and video-sitemaps are not compliant)
3) find all urls within the sitemaps

for every URL in the sitemap - run a Core Web Vitals request to Chrome User Experience (CrUX) API.
for every succesfull request
    1) log the values to a .csv report file
    2) log a url of the successfully fetched call for processing within the next job
    3)if there are any errors caught when parsing the response - provide report

additionally a detailed log is being provided for every job ran.

the report with CWV data is stored in /output/cwv-report.csv
errors get reported in  /report/err-{date}-{domain}.txt
job log is stored at /log.txt



to give some more context - its not possible to know the URLs which will be in CrUX, so the approach to query all urls in the sitemap was taken.
also - as the urls in the CrUX report are changing - pages that were listed one day, might not be there the next day, so recommended approach is to run the job from start every time the job is commencing
