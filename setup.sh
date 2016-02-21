#Reading the sensor (https://github.com/alaudet/hcsr04sensor)
sudo apt-get install python-pip
sudo pip install hcsr04sensor
#Sending to Google Spreadsheets (https://github.com/JeremyMorgan/Raspberry_Pi_Weather_Station)
pip install --upgrade oauth2client
pip install gspread
#maybe: pip install PyOpenSSL
#Supervisord
sudo pip install supervisord