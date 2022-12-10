from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import datetime as dt
import json

#settings
work_start_time = dt.time(hour=9, minute=0)
work_end_time = dt.time(hour=15, minute=0)
excluded_weekdays=[] #["Sat","Sun"]False
numberofdaysout=2
using_family_calendar=True #note, the "famly" calendar is screwed up and set for UTC, I timeshift all events -8 hours in the code below

# Setup the Calendar API
def pullevents():
    # setup the calendar api    
    SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
    store = file.Storage(r'/Users/bentonwilliams/Projects/tokens/credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(r'/Users/bentonwilliams/Projects/tokens/client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    # Calendar API parameters
    now=dt.datetime.utcnow()
    startdate = now.isoformat() + 'Z' #indicates UTC time
    
    enddate=(now.replace(hour=0,minute=0,day=now.day+1)+dt.timedelta(days=numberofdaysout)).isoformat()+'Z'

    print('Getting the upcoming 10 events')

    # get calendar IDs
    # page_token = None
    # while True:
    #     calendar_list = service.calendarList().list(pageToken=page_token).execute()
        
    #     for calendar_list_entry in calendar_list['items']:
    #         print (calendar_list_entry['summary'])

    #     page_token = calendar_list.get('nextPageToken')
    #     if not page_token:
    #         break
    # cal_list_json=json.dumps(calendar_list,indent=4)
    # with open("calendarlist.json","w") as cl:
    #     cl.write(cal_list_json)
    
    # Call the calendar api
    family_cal_id="family17018163637418122965@group.calendar.google.com"
    primary_cal_id="primary"
    calendar_id_used=family_cal_id
    events_result = service.events().list(calendarId=calendar_id_used,
                                    timeMin=startdate,
                                    timeMax=enddate, 
                                    singleEvents=True,
                                    orderBy='startTime').execute()

    events = events_result.get('items', [])
    if not events:
        print('No upcoming events found.')
    else:
        json_calendars=json.dumps(events,indent=4)
        with open("calevents.json","w") as f:
            f.write(json_calendars)
    ##testing - find the timestamp format from this calendar
    print("here is the timestamp format from the first event in this calendar, completely untouched")
    ts=events[0]['start'].get('dateTime',events[0].get('date'))
    print(ts)
    print() 
    
    
    return events

def createeventlist(events):
    #correction to account for screwed up family calendar
    correction=dt.timedelta(days=0)
    if using_family_calendar: correction=dt.timedelta(hours=-8)

    #take the json of events data
    #create a list of lists where the elements are [eventstart-datetime, eventend-datetime]
    eventlist=[]
    for event in events:
        ts_start=event['start'].get('dateTime').replace("Z","") #starting timestamp, remove the z if not tz offset
        start=dt.datetime.fromisoformat(ts_start)+correction
        ts_end=event['end'].get('dateTime').replace("Z","") #starting timestamp, remove the z if not tz offset
        end=dt.datetime.fromisoformat(ts_end)+correction
        eventlist.append([start,end])
        print (f'{start.strftime("%m/%d T %X")} to {end.strftime("%m/%d T %X")}') 
    
    return eventlist

def bookedevents(events):
    def mergeevents(a,b):
        if (a[1]>=b[0] and a[1] <= b[1]) or a[0]>=b[0] and a[0]<=b[1] or b[0]>=a[0] and b[0]<=a[1] or b[1]>=a[0] and b[1]<=a[1]:
            return [min(a[0],b[0]),max(a[1],b[1])],None
        else:
            return a,b

    ans=[events[0]]
    for i in range(1,len(events)):
        a,b=mergeevents(ans[-1],events[i])
        #print(a,b)
        if b==None: 
            ans[-1]=a
        else: 
            ans.append(b)
    for x in ans:
        print(f'{x[0].month}/{x[0].day}T{x[0].hour}:{x[0].minute}',end="  -  ")
        print(f'{x[1].month}/{x[1].day}T{x[1].hour}:{x[1].minute}')
    return ans

def sortblocksbydate(eventlist):
    calendar={}
    for eventblock in eventlist:
        curday=eventblock[0].replace(hour=0,minute=0)
        calendar[curday]=calendar.get(curday,[])+([[eventblock[0],eventblock[1]]])
    # for day in calendar:
    #     print (day, calendar[day])
    return calendar

def printopenblocks(calendar):
    days=[days for days in calendar]
    days.sort()
    for day in days:
        print(day.strftime("%m-%d %a : "),end="")
        #set beginning of the day
        s=day 
        for i in range(0,len(calendar[day])):
            #end = beginning of first block
            e=calendar[day][i][0]
            if s<e: print(f'{s.hour}:{s.minute}-{e.hour}:{e.minute}, ',end="")
            s=calendar[day][i][1]
        e=day+dt.timedelta(days=1)
        print(f'{s.hour}:{s.minute}-{e.hour}:{e.minute}')
             



def clipblocks(openblocks):
    clippedopenblocks=[]
    h_0=work_start_time.hour
    m_0=work_start_time.minute
    h_1=work_end_time.hour
    m_1=work_end_time.minute
    #if the block starts after window or block ends before window, False
    for block in openblocks:
        
        start=block[0]
        end=block[1]
        dtzero=start.replace(hour=h_0, minute=m_0)
        dtone=start.replace(hour=h_1, minute=m_1)
        if start<dtzero and end>dtzero:
            start=dtzero
        if end>dtone and start<dtone:
            end=dtone
        if end>dtzero and start<dtone:
            clippedopenblocks.append((start,end))
    return clippedopenblocks
        
# def correcttimezone(timestamp):
#     for event in events:


def printblocks(openblocks):
    day1=openblocks[0][0]
    daylist=[day1]
    for _ in range(10):
        day1=day1.replace(day=day1.day+1)
        daylist.append(day1)

    print("printing for pasting...")
    cur=openblocks[0][0]
    dayblocks=[]
    #print date:
    month=str(int(cur.strftime("%m")))
    day=str(int(cur.strftime("%d")))
    print(f'{month}/{day} {cur.strftime("%a")}:',end=" ")
    #print(cur.strftime("%a %m/%d"),end=": ")
    
    for block in openblocks:
        start=block[0]
        end=block[1]
        dayname=start.strftime("%a")
        if start.day!=cur.day:
            
            month=str(int(start.strftime("%m")))
            day=str(int(start.strftime("%d")))
            if dayname not in excluded_weekdays: 
                print()
                print(f'{month}/{day} {start.strftime("%a")}:',end=" ")
            cur=start
        if start.day==cur.day and dayname not in excluded_weekdays:
            for t in [start,end]:
                hour=int(t.strftime("%I"))
                minute=":"+t.strftime("%M")
                if minute==":00": minute=""
                if t.strftime("%p")=="AM": ampm="a"
                if t.strftime("%p")=="PM": ampm="p"
                if t==start: dash='-'
                else: dash=" "
                print(f'{hour}{minute}',end=dash)
            #print(start.strftime("%I:%M%p")+"-"+end.strftime('%I:%M%p'),end=" ")
            
def main():
    events=pullevents()
    eventlist=createeventlist(events)
    consoldatedevents=bookedevents(eventlist)
    caldict=sortblocksbydate(consoldatedevents)
    printopenblocks(caldict)


main()


