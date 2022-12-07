from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import datetime as dt
import json



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
    startdate = now.isoformat() + 'Z' # 'Z' indicates UTC time
    numberofdaysout=10
    enddate=(now+dt.timedelta(days=numberofdaysout)).isoformat()+'Z'

    print('Getting the upcoming 10 events')

    # Call the calendar api
    events_result = service.events().list(calendarId='primary',
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
    return events

def clipblocks(openblocks):
    clippedopenblocks=[]
    h_0=9
    m_0=0
    h_1=17
    m_1=0
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
        

def findopenblocks(events):
    end=dt.datetime.fromisoformat(events[0]['start'].get('dateTime',events[0].get('date')))
    end=end.replace(hour=0,minute=0)
    openblocks,bookedblocks=[],[]
    for event in events:
        start= dt.datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
        if start>end:  
            openblocks.append((end,start))
        end = dt.datetime.fromisoformat(event['end'].get('dateTime'))
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
            if dayname not in ["Sat","Sun"]: 
                print()
                print(f'{month}/{day} {start.strftime("%a")}:',end=" ")
            cur=start
        if start.day==cur.day and dayname not in ["Sat","Sun"]:
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


