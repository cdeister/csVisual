from Adafruit_IO import Client

curSubj=['ci01','ci02','ci03','ci04']

# Connect to MQTT broker.
yourHashPath='/Users/cad/simpHashes/cdIO.txt'
simpHash=open(yourHashPath)
aio = Client(simpHash.read())

curSubj=['ci01','ci02','ci03','ci04','ci05','an1']