# -*- coding: utf-8 -*-
"""
Created on Thu Sep 28 21:44:26 2017

@author: Alex
"""

# Ads matter?

# Youtube Scraping

import requests
import bs4
import pandas as pd
from threading import Thread
from queue import Queue
import time

df = pd.DataFrame()

start = time.time()

query = "python"

rootURL = 'https://www.youtube.com'
socialblade = 'https://socialblade.com/youtube'
URLTail = '/results?sp=EgIQAVAU&q=' & query

pool_size = 5

searchResponse = requests.get(rootURL + URLTail)
searchSoup = bs4.BeautifulSoup(searchResponse.text, "lxml")

# 2d dictionary
youtubers = {} # Attributes: number, total views, subs, socialblade data. This is what will be displayed 
youtuberKeys = [] # just the name

videoData = searchSoup.select('div.yt-lockup-content')
# this "video list" is what I want to thread. 8 threads

q = Queue()
#map(q.put, videoData)
for video in videoData:
    q.put(video)

def getVidStats(video): 
    viewData = video.select('.yt-lockup-meta > ' + \
                     '.yt-lockup-meta-info')[0]
    
    # This will be the check for ads or not. Will only process vids with both views and upload date
    if len(viewData) > 1:
        viewCount = int(viewData.select('li:nth-of-type(2)')[0]\
                   .get_text()[:-6].replace(",", ""))

        if viewCount >= 5000:
        #if viewCount >= 1000000:
            channel = video.select('.yt-lockup-byline')[0].get_text()
            # Only append if it doesn't already exist
            if channel in youtubers:
                youtubers[channel]["viewTotal"] += viewCount
                youtubers[channel]["resultCount"] += 1
            else:
                youtuberKeys.append(channel)
                youtubers[channel] = {}
                youtubers[channel]["viewTotal"] = viewCount
                youtubers[channel]["resultCount"] = 1
                # need to find channel link
                youtubers[channel]["link"] = video.select('.yt-lockup-byline a')[0]['href']
            
                socialURL = socialblade + youtubers[channel]["link"]
                socialResponse = requests.get(socialURL)
                socialSoup = bs4.BeautifulSoup(socialResponse.text, "lxml")
            
                # Top Header Info
                headerInfo = socialSoup.select('div.YouTubeUserTopInfo')
                
                
                if len(headerInfo) > 0:
                    monthViews = int(socialSoup.select('#afd-header-views-30d')[0].get_text().replace(",", ""))
                    monthSubs = int(socialSoup.select('#afd-header-subs-30d')[0].get_text().replace(",", ""))
                    youtubers[channel]["MonthViews"] = monthViews 
                    youtubers[channel]["MonthSubs"] = monthSubs
                    
                    youtubers[channel]["UploadCount"] = int(socialSoup.select('#youtube-stats-header-uploads')[0].get_text())
                    youtubers[channel]["Subs"] = int(socialSoup.select('#youtube-stats-header-subs')[0].get_text())
                    youtubers[channel]["TotalViews"] = int(socialSoup.select('#youtube-stats-header-views')[0].get_text())
                    youtubers[channel]["Category"] = socialSoup.select('#youtube-stats-header-channeltype')[0].get_text().capitalize()
                    youtubers[channel]["CreationDate"] = headerInfo[-1].select('span:nth-of-type(2)')[0].get_text()
                else:
                    youtubers[channel]["MonthViews"] = -1 
                    youtubers[channel]["MonthSubs"] = -1
                    youtubers[channel]["UploadCount"] = -1
                    youtubers[channel]["Subs"] = -1
                    youtubers[channel]["TotalViews"] = -1
                    youtubers[channel]["Category"] = "Not Found"
                    youtubers[channel]["CreationDate"] = "Not Found"
            
                # Don't forget calculated values and ranking

def videoWorker(q):
    while not q.empty():
        video = q.get()
        
        getVidStats(video)
        q.task_done()

for x in range(pool_size):
    t = Thread(target = videoWorker, args = (q,))
    #print(x)
    t.start()

q.join()


def printList():
    global youtubers, youtuberKeys
    attributes = ["viewTotal", "resultCount", "link", "MonthViews", "MonthSubs",\
                  "UploadCount", "Subs", "TotalViews","Category", "CreationDate"]
    
    for channel in youtuberKeys:
        print("---" + channel + "---")
        ch = youtubers[channel]
        for atr in attributes:
            print(atr + ":", ch[atr])
        print()

def getDataFrame():
    global youtubers, youtuberKeys
    arr = []
    for youtuber in youtuberKeys:
        youtubers[youtuber]["name"] = youtuber
        arr.append(youtubers[youtuber])
    return pd.DataFrame(arr)
    

print('Job took:', time.time()-start)
