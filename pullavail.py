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
    store = file.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    # Calendar API parameters
    now=dt.datetime.utcnow()
    startdate = now.isoformat() + 'Z' # 'Z' indicates UTC time
    numberofdaysout=3
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


def findopenblocks(events):
    bob=dt.datetime.fromisoformat(events[0]['start'].get('dateTime',events[0].get('date')))
    bob=bob.replace(hour=0)
    openblocks,bookedblocks=[],[]
    for event in events:
        a = dt.datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
        if a>bob: openblocks.append((bob,a))
        bob = dt.datetime.fromisoformat(event['end'].get('dateTime'))
        bookedblocks.append((a,bob))

    #print(openblocks)
    for i in range(0,len(bookedblocks)):
        print(bookedblocks[i][0].strftime("%m/%d T %X"),end=" -")
        print(bookedblocks[i][1].strftime("%m/%d T %X"))
    for i in range(0,len(openblocks)):
        print(openblocks[i][0].strftime("%m/%d T %X"),end=" -")
        print(openblocks[i][1].strftime("%m/%d T %X"))
    return openblocks

def printblocks(openblocks):
    earliest_start_hour=9
    latest_end_hour=17
    cur_day=openblocks[0][0]
    dayblocks=[]
    for i in range(0,len(openblocks)):
        #print(openblocks[i])
        a=openblocks[i][0]
        # a=a.replace(hour=max(a.hour,earliest_start_hour),minute=0)
        # if a.hour>latest_end_hour: continue
       
        b=openblocks[i][1]
        # b=b.replace(hour=min(b.hour,latest_end_hour),minute=0)
         
        if a.day==cur_day.day:
            dayblocks.append(a.strftime("%I:%M%p")+"-"+b.strftime('%I:%M%p'))
        else:
            print(cur_day.strftime("%a (%m/%d)"),end=": ")
            for block in dayblocks:
                print (block,end=", ")
            print()
            cur_day=a
            dayblocks=[]   
        
def main():
    events=pullevents()
    #with open("calevents.json","r") as f:
    #    events=json.load(f)
    openblocks=findopenblocks(events)
    printblocks(openblocks)


main()


