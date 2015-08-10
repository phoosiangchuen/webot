from bs4 import BeautifulSoup
from urllib2 import urlopen
from urlparse import urljoin
import re

class Link(object):
    def __init__(self, url, text=''):
        self.url = url
        self.text = text

class CrawlStrategy(object):
    def crawl(self): pass
class CrawlJobstreet(object):
    def crawl(self):
        print 'crawl Jobstreet web page'
    
class Webpage(object):
    def __init__(self, link, html):
        self.link = Link(link.url, html.title.string.strip())
        self.html = html

class WebpageFactory(object):
    def parse(self, url): pass
class JobstreetWpFactory(WebpageFactory):
    def parse(self, link):
        html_source = urlopen(link.url).read()
        soup = BeautifulSoup(html_source, 'html.parser')
        wpage = Webpage(link, soup)
        pagination = wpage.html.find_all('a', id=re.compile('^page_'))
        paginationlist = [link.url] # Add current URL into pagination
        for a in pagination:
            absUrl = urljoin(link.url, a['href'])
            if absUrl not in paginationlist:
                paginationlist.append(absUrl)
        return wpage, paginationlist
class JobstreetJpFactory(WebpageFactory):
    def parse(self, link):
        html_source = urlopen(link.url).read()
        soup = BeautifulSoup(html_source, 'html.parser')
        wpage = Webpage(link, soup)
        return wpage
        
class Website(object):
    def __init__(self):
        self.pageIndex = 0
        self.pagesLimit = 4
        self.pagination = list()
    def load(self, link, factory=JobstreetWpFactory()):
        self.page, tempPagination = factory.parse(link)
        for p in tempPagination:
            if p not in self.pagination:
                self.pagination.append(p)
        self.history = [link.url]
    def searchJob(self, * keywords):
        stopIndex = self.pageIndex + self.pagesLimit
        stopIndex = len(self.pagination)-1 if stopIndex > len(self.pagination)-1 else stopIndex
        fh = open('webot_result.txt', 'w')
        # loop pages
        while self.pageIndex < stopIndex:
            print '[+]Page %d of %d.' % (self.pageIndex+1, stopIndex)
            print '  -->' + self.pagination[self.pageIndex]
            # loop jobs in current page
            jobs = self.page.html.find_all('a', id=re.compile('^position_title_'))
            jobsLink = [Link(a['href'], a.string.strip()) for a in jobs]
            self.processJobs(fh, jobsLink, keywords)
            # go to next page
            self.next()
        fh.close()
        
    def processJobs(self, filehandler, jobs, keywords, factory=JobstreetJpFactory()):
        for job in jobs:
            if job.url in self.history:
                pass # bypass if job url already exist in self.history
            else:
                matches = 0
                kwmatch = ''
                page = factory.parse(job)
                self.history.append(job.url)
                title_tag = page.html.find('h1', id=re.compile('^position_title'))
                loc_tag = page.html.find('span', id=re.compile('^single_work_location'))
                desc_tag = page.html.find('div', id=re.compile('^job_description'))
                if title_tag is None or loc_tag is None or desc_tag is None:
                    filehandler.write('[-]Fail to process ' + job.text.encode('utf-8') + ' page.\n')
                    filehandler.write(job.url + '\n')
                    pass
                else:
                    jobhead = '%s\n%s' % (title_tag.getText().strip().encode('utf-8'), loc_tag.getText().strip().encode('utf-8'))
                    jobbody = desc_tag.getText().strip().encode('utf-8')
                    for kw in keywords:
                        match = len([m.start() for m in re.finditer(kw.lower(), jobbody.lower())])
                        if match>0:
                            matches+= match
                            kwmatch+= '%d match for %s. ' % (match, kw)
                    if matches>0:
                        filehandler.write('[+]' + kwmatch.strip() +' in ' + jobhead + '\n')
                        filehandler.write(job.url + '\n\n')
                
    def next(self): 
        if self.pageIndex+1 >= len(self.pagination):
            raise RuntimeError('Reach end of page')
        else:
            self.pageIndex+= 1
            self.load(Link(self.getPageIndexUrl()))
    def previous(self): 
        if self.pageIndex == 0: 
            raise RuntimeError('Reach beginning of page')
        else:
            self.pageIndex-= 1
            self.load(Link(self.getPageIndexUrl()))
    def getPageIndexUrl(self, index=-1):
        index = self.pageIndex if index==-1 else index
        return self.pagination[index]
    def visited(self, url=''): 
        return url in self.history
    
#link = Link('http://job-search.jobstreet.com.my/malaysia/job-opening.php', 'Jobstreet.com')
link = Link('http://job-search.jobstreet.com.my/malaysia/job-opening.php?key=&location=&specialization=191%2C192%2C193&area=&salary=&src=12&search_submit=1', 'Jobstreet.com')
factory = JobstreetWpFactory()
wsite = Website()
wsite.load(link)

wsite.pagesLimit = 6
wsite.searchJob('Senior Manager', 'Sr. Manager', 'IT Manager', 'Development')
wsite.searchJob('Senior Manager', 'Sr. Manager', 'IT Manager', 'Development')

