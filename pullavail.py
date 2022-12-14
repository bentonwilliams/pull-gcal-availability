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
numberofdaysout=7
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



def findopenblocks(events):
    ts=events[0]['start'].get('dateTime',events[0].get('date')).replace("Z","")
    end=dt.datetime.fromisoformat(ts)
    
    # if calendar is the family calendar, add a negative 8hour timedelta
    if using_family_calendar: end=end+dt.timedelta(hours=-8)
    
    end=end.replace(hour=0,minute=0)
    openblocks,bookedblocks=[],[]
    for event in events:
        ts=event['start'].get('dateTime', event['start'].get('date')).replace("Z","")
        start= dt.datetime.fromisoformat(ts)
        
        #adjusting for screwed up family calendar
        if using_family_calendar: start=start+dt.timedelta(hours=-8)
        
        if start>end:  
            openblocks.append((end,start))
        ts=event['end'].get('dateTime').replace("Z","")    
        end = dt.datetime.fromisoformat(ts)
        if using_family_calendar: end=end+dt.timedelta(hours=-8)
        bookedblocks.append((start,end))
    last=start.replace(day=start.day+1,hour=0,minute=0,second=0)
    if last>end: openblocks.append((end,last))
    openblocks=clipblocks(openblocks)
    #print(openblocks)
    print("printing booked blocks:")
    for i in range(0,len(bookedblocks)):
         print(bookedblocks[i][0].strftime("%m/%d T %X"),end=" -")
         print(bookedblocks[i][1].strftime("%m/%d T %X"))
    print("Printing open blocks")
    for i in range(0,len(openblocks)):
        print(openblocks[i][0].strftime("%m/%d T %X"),end=" -")
        print(openblocks[i][1].strftime("%m/%d T %X"))
    return openblocks

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
    #with open("calevents.json","r") as f:
    #    events=json.load(f)
    openblocks=findopenblocks(events)
    printblocks(openblocks)


main()


