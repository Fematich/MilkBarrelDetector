trig_pin = 14
echo_pin = 15
unit = 'metric'  # choices (metric or imperial)
temperature = 20  # Celcius for metric, Fahrenheit for imperial
round_to = 1  # report a cleaner rounded output.
avg_samplesize=8
#IFTTT
api_key="YOURKEYHERE"
#gspread
servicejson="PATHTOSERVICEACCOUNT"
workbook="MILK_AUTOMAT"
measurement_sheet="measurements"
refill_sheet="refills"
#barrel logic
MAX_DEPTH=70 #in cm
SURFACE=0.12566370614359174#pi*0.2**2 in m2
ALARM_VOLUME=5
TRIGGER_VOLUME=12
MIN_REFILL=6
PRECISION=1
MAX_VOLUME=80