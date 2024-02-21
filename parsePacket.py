from threading import Thread
from queue import Queue
from serial import serial_for_url, SerialException
import struct

event_names =  ["Preflight",
                "Liftoff",
                "Booster Burnout",
                "Apogee Detected",
                "Firing Apogee Pyro",
                "Separation Detected!",
                "Firing Mains",
                "Under Chute",
                "Ejecting Booster",
                "Firing 2nd Stage",
                "2nd Stage Ignition",
                "2nd Stage Burnout",
                "Firing Airstart1",
                "Airstart1 Ignition",
                "Airstart1 Burnout",
                "Firing Airstart2",
                "Airstart2 Ignition",
                "Airstart2 Burnout",
                "NoFire: Rotn Limit",
                "NoFire: Alt Limit",
                "NoFire: Rotn/Alt Lmt",
                "Booster Apogee",
                "Booster Apogee Fire",
                "Booster Separation!",
                "Booster Main Deploy",
                "Booster Under Chute",
                "Time Limit Exceeded",
                "Touchdown!",
                "Power Loss! Restart!",
                "Booster Touchdown!",
                "Booster Preflight",
                "Booster Time Limit",
                "Booster Pwr Restart"]   

class PacketParser(object):
    """
    packed preflight message format:
    appears to be variable length because of rocketName and radio callsign
    but in all places the name seems limit to 20 char, and we dont care about callsign

    format appears to be:
    [byte number: name: c-type: python struct-type]
    0:      radio.event:            unsigned byte   (B)
    1:      gnss.fix:               bool            (?)
    2:      cont.reportCode:        unsigned byte   (B)
    3-22:   settings.rocketName:    char[20]        (20s)
    23-24:  radio.baseAlt:          signed int16    (h)
    25-26:  radio.GPSalt:           signed int16    (h)
    27-30:  GPS.location.lat:       signed int32    (i)    
    31-34:  GPS.location.lng:       signed in32     (i)
    35-36:  radio.satNum:           unsigned int16  (H, maybe h) 
    37+     we ignore as they only relate to FHSS
    """
    pre_flight_format = "B ? B 20s h h i i H"





    def __init__(self, port: str, queue: Queue = None, timeout: int = 1) -> None:
        assert port is not None
        assert queue is not None

        self.serial = serial_for_url(port, do_not_open=True)
        self.serial.timeout = timeout
        self.queue = queue

        try:
            self.serial.open()
        except SerialException as e:
            print(f"Could not open serial port {self.serial.name}: {e}")
            
    def stop(self):
        self.stopped = True
        
    def run(self):
        self.alive = True
        self.thread_read = Thread(target=self.read_serial)
        self.thread_read.daemon = True
        self.thread_read.name = 'serial->socket'
        self.thread_read.start()
        
        self.writer()

    def reader(self):
        """loop forever and parse packet"""
        
        print("reader thread started")
        
        while self.alive:
            try:
                line = self.serial.readline()
                if line:
                    self.parse_packet(line)
            
            except SerialException as e:
                print(f"Could not open serial port {self.serial.name}: {e}")
                break

        self.alive = False
        print("reader thread terminated")        

    def parse_packet(self, packet: bytes):

        event = packet[0]

        if event == 0 or event == 30:
            """preflight packet"""

            self.parse_preflight(packet)

        elif event < 26:
          self.parse_inflight(packet)

        elif event == 26 or event == 27 or event == 29 or event == 31:
            self.parse_postflight(packet)


    def parse_preflight(self, packet):

        pass

    def parse_in_flight(self, packet):
# //inflight output variables
# //---------------------------
# uint16_t sampleTime;
# int16_t signalStrength=0;
# int16_t velocity = 0;
# int16_t Alt=0;
# int16_t spin=0;
# int16_t offVert=0;
# int16_t accel=0;
# int16_t packetNum = 0;
# boolean apogee = false;
# unsigned long lastSustainerRX = 0UL;
# unsigned long lastBoosterRX = 0UL;
        pass

    def parse_post_flight(self, packet):
# //Postflight output variables
# //---------------------------
# int maxAltitude=0;
# int maxVelocity=0;
# int maxG=0;
# int maxGPSalt=0;
# //GPS output variables
# byte GPSlock;
# int GPSalt=0;
# int prevGPSalt;
# char charGPSlat;
# float GPSlatitude;
# char charGPSlon;
# float GPSlongitude;
# float lastGPSlat;
# float lastGPSlon;
# float prevGPSlat = 0.0;
# float prevGPSlon = 0.0;
# unsigned long lastGPSfix = 0UL;
        pass


# //---------------------------
# //Data Packet variables
# //---------------------------
# uint8_t len;
# uint8_t len1;
# uint8_t len2;
# byte dataPacket1[66];
# byte dataPacket2[66];
# char dataString[256];
# boolean SDstatus = false;
# char sustainerFileName[13] = "FLIGHT01.txt";
# char boosterFileName[14] = "BOOSTER01.txt";
# boolean sustainerFileOpen = false;
# boolean boosterFileOpen = false;
# boolean sustainerFileCreated = false;
# boolean boosterFileCreated = false;
# byte n = 0;
# byte fileNum = 1;
# byte pktPosn = 0;
# int16_t packetnum = 0;
# unsigned long timer = 0UL;
# boolean radio1status = false;
# boolean radio2status = false;
# boolean sendPacket = true;
# boolean testMode = false;
# unsigned long testStart = 0UL;
# unsigned long lastRX = 0UL;
# unsigned long debugStart = 0UL;
# unsigned long debugStop = 0UL;
# unsigned long colorStart;
# int battVolt;
# boolean SDinit = false;
# boolean LCDinit = true;
# boolean parseSustainer = false;
# boolean parseBooster = false;
# uint32_t timeLastNMEA = 0UL;
# bool ledLight = false;
# //---------------------------
# //preflight output variables
# //---------------------------
# uint8_t event;
# int strPosn = 0;
# boolean signalEst = false;
# boolean dataProcessed = false;
# boolean sustainerPreFlightWrite = true;
# boolean boosterPreFlightWrite = true;
# boolean sustainerPostFlightWrite = true;
# boolean boosterPostFlightWrite = true;
# boolean boosterFileReady = false;
# unsigned long lostSignalTime = 2000000UL;
# byte j=0;



# /*---------------------------------------------------
#               PREFLIGHT PACKET
#  -----------------------------------------------------*/
    
#         //Read data from pre-flight packet
#         pktPosn=eventPosn;
#         event = (byte)rxPacket[pktPosn];//1
#         GPSlock = (byte)rxPacket[pktPosn];//2
#         contCode = (byte)rxPacket[pktPosn];//3
#         for(byte i=0;i<20;i++){rocketName[i] = (byte)rxPacket[pktPosn];}//23
#         radioInt.unionByte[0] = (byte)rxPacket[pktPosn];//24
#         radioInt.unionByte[1] = (byte)rxPacket[pktPosn];//25
#         baseAlt = radioInt.unionInt;
#         radioInt.unionByte[0] = (byte)rxPacket[pktPosn];//26
#         radioInt.unionByte[1] = (byte)rxPacket[pktPosn];//27
#         baseGPSalt = radioInt.unionInt;
#         charGPSlat = (int8_t)rxPacket[pktPosn];//28
#         for(byte i=0;i<4;i++){radioUnion.unionByte[i]=(byte)rxPacket[pktPosn];}//32
#         GPSlatitude=radioUnion.GPScoord;
#         charGPSlon = (byte)rxPacket[pktPosn];//33
#         for(byte i=0;i<4;i++){radioUnion.unionByte[i]=(byte)rxPacket[pktPosn];}//37
#         GPSlongitude=radioUnion.GPScoord;
#         radioInt.unionByte[0] = (byte)rxPacket[pktPosn];//38
#         radioInt.unionByte[1] = (byte)rxPacket[pktPosn];//39
#         satNum = radioInt.unionInt;
#         if(activeRadio->FHSS){
#           activeRadio->nextChnl = (byte)rxPacket[pktPosn];
#           activeRadio->nextChnl2 = (byte)rxPacket[pktPosn];
#           //set the next channel
#           activeRadio->syncFreq = false;
#           if(settings.debugSerial){
#             dispPktInfo();
#             Serial.print(F("Hopping Freq: "));}
#           activeRadio->chnlUsed = 0;
#           hopFreq();}
#         //capture the last good GPS coordinates to potentially store later in EEPROM
#         if(GPSlock == 1){
#           lastGPSlat = GPSlatitude;
#           lastGPSlon = GPSlongitude;}}

# void inflightPacket(byte rxPacket[]){
        
# /*---------------------------------------------------
#               INFLIGHT PACKET
#  -----------------------------------------------------*/     
        
#         //parse the GPS data and packet number first, then the samples
#         pktPosn = 52 + eventPosn;
#         radioInt.unionByte[0] = (byte)rxPacket[pktPosn];//53
#         radioInt.unionByte[1] = (byte)rxPacket[pktPosn];//54
#         packetnum = radioInt.unionInt;

#         if(debugSerial){Serial.print(F("Inflight Packet Received, PktNum: "));Serial.println(packetnum);}
        
#         if(activeRadio->FHSS){
#           activeRadio->nextChnl = (byte)rxPacket[pktPosn];
#           activeRadio->nextChnl2 = (byte)rxPacket[pktPosn];}
#         radioInt.unionByte[0] = (byte)rxPacket[pktPosn];//55
#         radioInt.unionByte[1] = (byte)rxPacket[pktPosn];//56
#         GPSalt = radioInt.unionInt;
#         for(byte j=0;j<4;j++){radioUnion.unionByte[j]=(byte)rxPacket[pktPosn];}//60
#         GPSlatitude=radioUnion.GPScoord;
#         for(byte j=0;j<4;j++){radioUnion.unionByte[j]=(byte)rxPacket[pktPosn];}//64
#         GPSlongitude=radioUnion.GPScoord;
      
#         //determine GPS lock from the packet length
#         if(len < 60+eventPosn){GPSlock = 0;}
#         else{GPSlock = 1; lastGPSfix = micros();}
        
#         //parse inflight packet of 4 samples
#         pktPosn = eventPosn;
#         for(byte i=0;i<4;i++){
                      
#           //parse the samples
#           event = (byte)rxPacket[pktPosn];//1
#           if(!apogee && event >=4 && event <=6){apogee = true;}
#           sampleTime = (byte)rxPacket[pktPosn];//2
#           sampleTime += ((byte)rxPacket[pktPosn] << 8);//3
#           radioInt.unionByte[0] = (byte)rxPacket[pktPosn];//4
#           radioInt.unionByte[1] = (byte)rxPacket[pktPosn];//5
#           velocity = radioInt.unionInt;
#           if(!apogee && velocity > maxVelocity){maxVelocity = velocity;}
#           radioInt.unionByte[0] = (byte)rxPacket[pktPosn];//6
#           radioInt.unionByte[1] = (byte)rxPacket[pktPosn];//7
#           Alt = radioInt.unionInt;
#           if(!apogee && Alt > maxAltitude){maxAltitude = Alt;}
#           radioInt.unionByte[0] = (byte)rxPacket[pktPosn];//8
#           radioInt.unionByte[1] = (byte)rxPacket[pktPosn];//9
#           spin = radioInt.unionInt;
#           radioInt.unionByte[0] = (byte)rxPacket[pktPosn];//10
#           radioInt.unionByte[1] = (byte)rxPacket[pktPosn];//11
#           offVert = radioInt.unionInt;
#           radioInt.unionByte[0] = (byte)rxPacket[pktPosn];//12
#           radioInt.unionByte[1] = (byte)rxPacket[pktPosn];//13
#           accel = radioInt.unionInt;
#           if(!apogee && accel > maxG){maxG = accel;}
          
#           //write to the SD card
#           if(SDinit){writeInflightData();}}

#         if(settings.debugSerial){Serial.println("Inflight Data Written");}
#         //set the next channel
#         if(activeRadio->FHSS){
#           activeRadio->syncFreq = false;
#           if(debugSerial){dispPktInfo();}
#           activeRadio->lastHopTime = activeRadio->lastRX - (packetnum%3 *200000UL);
#           activeRadio->chnlUsed = 0;
#           if(packetnum%3 == 0){
#             if(settings.debugSerial){Serial.print(F("Hopping Freq: "));}
#             hopFreq();}}

#         //capture the last good GPS coordinates to potentially store later in EEPROM
#         if(GPSlock == 1){
#           lastGPSlat = GPSlatitude;
#           lastGPSlon = GPSlongitude;}}

# void postflightPacket(byte rxPacket[]){
          
# /*---------------------------------------------------
#               POSTFLIGHT PACKET
#  -----------------------------------------------------*/
#         pktPosn = eventPosn+1;
#         maxAltitude = (byte)rxPacket[pktPosn];
#         maxAltitude += ((byte)rxPacket[pktPosn] << 8);
#         maxVelocity = (byte)rxPacket[pktPosn];
#         maxVelocity += ((byte)rxPacket[pktPosn] << 8);
#         maxG = (byte)rxPacket[pktPosn];
#         maxG += ((byte)rxPacket[pktPosn] << 8);
#         maxGPSalt = (byte)rxPacket[pktPosn];
#         maxGPSalt += ((byte)rxPacket[pktPosn] << 8);
#         GPSlock = (byte)rxPacket[pktPosn];
#         GPSalt = (byte)rxPacket[pktPosn];
#         GPSalt += ((byte)rxPacket[pktPosn] << 8);
#         charGPSlat = (byte)rxPacket[pktPosn];
#         for(byte i=0;i<4;i++){radioUnion.unionByte[i]=(byte)rxPacket[pktPosn];}
#         GPSlatitude=radioUnion.GPScoord;
#         charGPSlon = (byte)rxPacket[pktPosn];
#         for(byte i=0;i<4;i++){radioUnion.unionByte[i]=(byte)rxPacket[pktPosn];}
#         GPSlongitude=radioUnion.GPScoord;

#         //capture the last good GPS coordinates to potentially store later in EEPROM
#         if(GPSlock == 1){
#           lastGPSlat = GPSlatitude;
#           lastGPSlon = GPSlongitude;}
          
#         //write to the SD card
#         if(SDinit && parseSustainer && sustainerPostFlightWrite){writePostflightData();}
#         if(SDinit && parseBooster && boosterPostFlightWrite){writePostflightData();}

#         //sync the SD card
#         if(SDinit && parseSustainer){sustainerFile.flush();}
#         if(SDinit && parseBooster){boosterFile.flush();}
# }
