import datetime, time, requests, json, gspread
from collections import deque
from oauth2client.client import SignedJwtAssertionCredentials
import hcsr04sensor.sensor as sensor
import config

json_key = json.load(open(config.servicejson))
credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], ['https://spreadsheets.google.com/feeds'])
gc = gspread.authorize(credentials)

def send_ifttt_event(event, value1=None, value2=None, value3=None):
    "Send an event to the IFTTT maker channel"
    url = "https://maker.ifttt.com/trigger/{e}/with/key/{k}/".format(e=event,
                                                                     k=config.api_key)
    payload = {'value1': value1, 'value2': value2, 'value3': value3}
    return requests.post(url, data=payload)



def write_to_gspread(workbook,sheet,vals):
    try:
        wb = gc.open(workbook)
        ws=wb.worksheet(sheet)
        ws.append_row(vals)
    except Exception as ex:
        send_ifttt_event("melkautomaat_problems",value1="Unable to write to spreadsheet {w}/{s}".format(w=workbook,s=sheet),value2=str(vals),value3=str(ex))

def get_volume(measurement):
    return (config.MAX_DEPTH-measurement)*config.SURFACE*10

def strictly_increasing(L):
    return all(x<y for x, y in zip(L, L[1:]))

def contains_outliner(L,max_diff=1):
    L_avg=sum(L)/float(len(L))
    return all(abs(x-L_avg)>max_diff for x in L)

def measureloop():
    #  distance reading with the hcsr04 sensor module
    volumes=deque([None])
    logged_volumes=deque([None])
    value = sensor.Measurement(config.trig_pin, config.echo_pin, config.temperature, config.unit, config.round_to)
    in_refill=False
    alarm_sent=False
    last_volume=None
    filled_volume=None
    log_volume=0
    trig=0
    
    problems_sent=False

    while True:
        try:
            #measure the distance and ignore outliners
                #if one of the samples is outliner: ignore
                #if the samples are monotonically increasing: ignore
                #if the volume is too large (something before the sensor): ignore
            log_vol=False
            valid_vol=False
            dt_log=datetime.datetime.now()
            trials=0
            while not valid_vol and trials<10:
                vals=[]
                for i in range(config.avg_samplesize):
                    try:
                        vals.append(value.raw_distance())
                    except Exception as ex:
                        continue
                measurement=sum(vals)/float(config.avg_samplesize)
                volume=get_volume(measurement)
                if not (strictly_increasing(vals) or contains_outliner(vals)) and volume<config.MAX_VOLUME:
                    valid_vol=True
                else:
                    trials+=1
                    time.sleep(1)
            if trials>10 and not problems_sent:
                send_ifttt_event("melkautomaat_problems")
                problems_sent=True

            #calculate volume and get previous value
            if len(volumes)>10:
                last_volume=volumes.popleft()
            else:
                last_volume=volumes[-1]

            if len(logged_volumes)>10:
                last_logged_volume=logged_volumes.popleft()
            else:
                last_logged_volume=logged_volumes[-1]

            if not last_logged_volume:
                log_volume=volume
            else:
                if abs(volume-last_logged_volume)>=config.PRECISION:
                    log_volume=volume
            print "---------------------------"
            print "---------------------------"
            print "log_volume:         "+str(log_volume)
            print "last_logged_volume: " +str(last_logged_volume)
            print "last_volume:        "+str(last_volume)
            print "filled_volume:      "+str(filled_volume)
            print "---------------------------"

            #detect if barrel is removed (getting cleaned)
            if volume<=0:
                if not in_refill:
                    #log last not logged volume
                    write_to_gspread(config.workbook,config.measurement_sheet,[dt_log,"N/A",last_volume,last_volume-last_logged_volume if (last_volume and last_logged_volume) else 0])
                    logged_volumes.append(last_volume)
                    in_refill=True
                print "state: empty"
            #detect if it needs a refill
            if volume<config.ALARM_VOLUME and not in_refill and not alarm_sent:
                send_ifttt_event("melkautomaat_leeg")
                alarm_sent=True
                print "state:almost empty"

            if last_volume:
                #detect if barrel is refilled (was not empty, but is filled anyway)
                if not in_refill and volume>last_volume+config.MIN_REFILL:
                    alarm_sent=False
                    #log last not logged volume
                    print "state:refilled but not empty"
                    write_to_gspread(config.workbook,config.measurement_sheet,[dt_log,"N/A",last_volume,last_volume-last_logged_volume if (last_volume and last_logged_volume) else 0])
                    logged_volumes.append(last_volume)
                    write_to_gspread(config.workbook,config.refill_sheet,[dt_log,'NO',last_volume,volume,filled_volume-last_volume if (last_volume and filled_volume) else 0,volume-last_volume if last_volume else 0])
                    log_volume=volume
                    filled_volume=volume
                    log_vol=True

                #detect if barrel is replaced
                if in_refill and volume>last_volume+config.MIN_REFILL:
                    print "state:refilled and empty"
                    in_refill=False
                    alarm_sent=False
                    write_to_gspread(config.workbook,config.refill_sheet,[dt_log,'YES',last_volume,volume,filled_volume-last_volume if (last_volume and filled_volume) else 0,volume-last_volume if last_volume else 0])
                    log_volume=volume
                    filled_volume=volume
                    log_vol=True

            #calculate sleeping time and write to spreadsheet if logging is required
            dt_now=datetime.datetime.now()
            delay=(dt_now - dt_log).seconds
            log_vol=True
            trig=0
            #log measurements to google spreadsheets
            if log_vol:
                print str([dt_log,measurement,log_volume,log_volume-last_logged_volume if last_logged_volume else 0])
                write_to_gspread(config.workbook,config.measurement_sheet,[dt_log,measurement,log_volume,log_volume-last_logged_volume if last_logged_volume else 0])
                logged_volumes.append(volume)
            #store last volume and sleep
            trig+=1
            volumes.append(volume)
            time.sleep(1)
        except Exception as ex:
            raise
            # send_ifttt_event("melkautomaat_problems",value1=str(ex))

if __name__ == "__main__":
    measureloop()