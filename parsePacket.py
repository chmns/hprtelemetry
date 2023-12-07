


# //---------------------------
# //Code Control Option variables
# //---------------------------
# boolean displayStandard = true;
# boolean FHSS = false;
# boolean debugSerial = true;
# float unitConvert = 3.28084F;
# boolean LCD = true;
# boolean GPSdebug = true;


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
# //---------------------------
# //preflight output variables
# //---------------------------
# char rocketName[20]="";
# int baseAlt=0;
# int baseGPSalt = 0;
# byte contCode;
# int satNum = 0;
# boolean fileOpen = true;
# //---------------------------
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
# //---------------------------
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
# //---------------------------
# //Radio Variables
# //---------------------------
# union {
#    float GPScoord;
#    unsigned long radioTime;
#    byte unionByte[4];
# } radioUnion;
# union {
#    int16_t unionInt;
#    byte unionByte[2]; 
# } radioInt;
# byte chnl1 = 0;
# byte chnl2 = 0;
# byte hailChnl_1 = 0;
# byte hailChnl_2 = 0;
# byte nextChnl;
# byte nextChnl2;
# boolean syncFreq = false;
# float freq1;
# float freq2;
# unsigned long lastHopTime = 0UL;
# byte chnlUsed = 0;
# boolean band433 = false;
# //---------------------------
# //LCD Variables
# //---------------------------
# byte whiteIntensity = 125;
# byte redIntensity = 255;
# byte greenIntensity = 255;
# byte blueIntensity = 255;
# byte flightPhase = 0;
# //---------------------------
# //BlueTooth Variables
# //---------------------------
# boolean blueTooth = true;
# //---------------------------
# //Event Table
# //---------------------------
# const char event_00[] PROGMEM = "Preflight";
# const char event_01[] PROGMEM = "Liftoff";
# const char event_02[] PROGMEM = "Booster Burnout";
# const char event_03[] PROGMEM = "Apogee Detected";
# const char event_04[] PROGMEM = "Firing Apogee Pyro";
# const char event_05[] PROGMEM = "Separation Detected!";
# const char event_06[] PROGMEM = "Firing Mains";
# const char event_07[] PROGMEM = "Under Chute";
# const char event_08[] PROGMEM = "Ejecting Booster";
# const char event_09[] PROGMEM = "Firing 2nd Stage";
# const char event_10[] PROGMEM = "2nd Stage Ignition";
# const char event_11[] PROGMEM = "2nd Stage Burnout";
# const char event_12[] PROGMEM = "Firing Airstart1";
# const char event_13[] PROGMEM = "Airstart1 Ignition";
# const char event_14[] PROGMEM = "Airstart1 Burnout";
# const char event_15[] PROGMEM = "Firing Airstart2";
# const char event_16[] PROGMEM = "Airstart2 Ignition";
# const char event_17[] PROGMEM = "Airstart2 Burnout";
# const char event_18[] PROGMEM = "NoFire: Rotn Limit";
# const char event_19[] PROGMEM = "NoFire: Alt Limit";
# const char event_20[] PROGMEM = "NoFire: Rotn/Alt Lmt";
# const char event_21[] PROGMEM = "Booster Apogee";
# const char event_22[] PROGMEM = "Booster Apogee Fire";
# const char event_23[] PROGMEM = "Booster Separation!";
# const char event_24[] PROGMEM = "Booster Main Deploy";
# const char event_25[] PROGMEM = "Booster Under Chute";
# const char event_26[] PROGMEM = "Time Limit Exceeded";
# const char event_27[] PROGMEM = "Touchdown!";
# const char event_28[] PROGMEM = "Power Loss! Restart!";
# const char event_29[] PROGMEM = "Booster Touchdown!";
# const char event_30[] PROGMEM = "Booster Preflight";
# const char event_31[] PROGMEM = "Booster Time Limit";
# const char event_32[] PROGMEM = "Booster Pwr Restart";

# const char *const eventTable[] PROGMEM = {
#   event_00, event_01, event_02, event_03, event_04,
#   event_05, event_06, event_07, event_08, event_09,
#   event_10, event_11, event_12, event_13, event_14,
#   event_15, event_16, event_17, event_18, event_19,
#   event_20, event_21, event_22, event_23, event_24,
#   event_25, event_26, event_27, event_28, event_29,
#   event_30, event_31, event_32};

# byte greenEvents[] = {5,6,7};
# byte redEvents[] = {18, 19, 20, 26, 28};

# //---------------------------
# //Pyro Code Table
# //---------------------------
# const char cont_0[] PROGMEM = "No Pyros Detected!";
# const char cont_1[] PROGMEM = "No Continuity Pyro 1";
# const char cont_2[] PROGMEM = "No Continuity Pyro 2";
# const char cont_3[] PROGMEM = "No Continuity Pyro 3";
# const char cont_4[] PROGMEM = "No Continuity Pyro 4";
# const char cont_5[] PROGMEM = "All 3 Pyros Detected";
# const char cont_6[] PROGMEM = "All 4 Pyros Detected";
# const char cont_7[] PROGMEM = "Pyro Apogee Only";
# const char cont_8[] PROGMEM = "Pyro Mains Only";
# const char cont_9[] PROGMEM = "Pyro Mains & Apogee";

# byte greenCont[5] = {5, 6, 7, 8, 9};
# byte redCont[5]   = {0, 1, 2, 3, 4};

# const char *const pyroTable[] PROGMEM = {
#   cont_0, cont_1, cont_2, cont_3, cont_4, 
#   cont_5, cont_6, cont_7, cont_8, cont_9};


# void preflightPacket(byte rxPacket[]){
  
# /*---------------------------------------------------
#               PREFLIGHT PACKET
#  -----------------------------------------------------*/
    
#         //Read data from pre-flight packet
#         pktPosn=eventPosn;
#         event = (byte)rxPacket[pktPosn];pktPosn++;//1
#         GPSlock = (byte)rxPacket[pktPosn];pktPosn++;//2
#         contCode = (byte)rxPacket[pktPosn];pktPosn++;//3
#         for(byte i=0;i<20;i++){rocketName[i] = (byte)rxPacket[pktPosn];pktPosn++;}//23
#         radioInt.unionByte[0] = (byte)rxPacket[pktPosn];pktPosn++;//24
#         radioInt.unionByte[1] = (byte)rxPacket[pktPosn];pktPosn++;//25
#         baseAlt = radioInt.unionInt;
#         radioInt.unionByte[0] = (byte)rxPacket[pktPosn];pktPosn++;//26
#         radioInt.unionByte[1] = (byte)rxPacket[pktPosn];pktPosn++;//27
#         baseGPSalt = radioInt.unionInt;
#         charGPSlat = (int8_t)rxPacket[pktPosn];pktPosn++;//28
#         for(byte i=0;i<4;i++){radioUnion.unionByte[i]=(byte)rxPacket[pktPosn];pktPosn++;}//32
#         GPSlatitude=radioUnion.GPScoord;
#         charGPSlon = (byte)rxPacket[pktPosn];pktPosn++;//33
#         for(byte i=0;i<4;i++){radioUnion.unionByte[i]=(byte)rxPacket[pktPosn];pktPosn++;}//37
#         GPSlongitude=radioUnion.GPScoord;
#         radioInt.unionByte[0] = (byte)rxPacket[pktPosn];pktPosn++;//38
#         radioInt.unionByte[1] = (byte)rxPacket[pktPosn];pktPosn++;//39
#         satNum = radioInt.unionInt;
#         if(activeRadio->FHSS){
#           activeRadio->nextChnl = (byte)rxPacket[pktPosn];pktPosn++;
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
#         radioInt.unionByte[0] = (byte)rxPacket[pktPosn];pktPosn++;//53
#         radioInt.unionByte[1] = (byte)rxPacket[pktPosn];pktPosn++;//54
#         packetnum = radioInt.unionInt;

#         if(debugSerial){Serial.print(F("Inflight Packet Received, PktNum: "));Serial.println(packetnum);}
        
#         if(activeRadio->FHSS){
#           activeRadio->nextChnl = (byte)rxPacket[pktPosn];pktPosn++;
#           activeRadio->nextChnl2 = (byte)rxPacket[pktPosn];pktPosn++;}
#         radioInt.unionByte[0] = (byte)rxPacket[pktPosn];pktPosn++;//55
#         radioInt.unionByte[1] = (byte)rxPacket[pktPosn];pktPosn++;//56
#         GPSalt = radioInt.unionInt;
#         for(byte j=0;j<4;j++){radioUnion.unionByte[j]=(byte)rxPacket[pktPosn];pktPosn++;}//60
#         GPSlatitude=radioUnion.GPScoord;
#         for(byte j=0;j<4;j++){radioUnion.unionByte[j]=(byte)rxPacket[pktPosn];pktPosn++;}//64
#         GPSlongitude=radioUnion.GPScoord;
      
#         //determine GPS lock from the packet length
#         if(len < 60+eventPosn){GPSlock = 0;}
#         else{GPSlock = 1; lastGPSfix = micros();}
        
#         //parse inflight packet of 4 samples
#         pktPosn = eventPosn;
#         for(byte i=0;i<4;i++){
                      
#           //parse the samples
#           event = (byte)rxPacket[pktPosn];pktPosn++;//1
#           if(!apogee && event >=4 && event <=6){apogee = true;}
#           sampleTime = (byte)rxPacket[pktPosn];pktPosn++;//2
#           sampleTime += ((byte)rxPacket[pktPosn] << 8);pktPosn++;//3
#           radioInt.unionByte[0] = (byte)rxPacket[pktPosn];pktPosn++;//4
#           radioInt.unionByte[1] = (byte)rxPacket[pktPosn];pktPosn++;//5
#           velocity = radioInt.unionInt;
#           if(!apogee && velocity > maxVelocity){maxVelocity = velocity;}
#           radioInt.unionByte[0] = (byte)rxPacket[pktPosn];pktPosn++;//6
#           radioInt.unionByte[1] = (byte)rxPacket[pktPosn];pktPosn++;//7
#           Alt = radioInt.unionInt;
#           if(!apogee && Alt > maxAltitude){maxAltitude = Alt;}
#           radioInt.unionByte[0] = (byte)rxPacket[pktPosn];pktPosn++;//8
#           radioInt.unionByte[1] = (byte)rxPacket[pktPosn];pktPosn++;//9
#           spin = radioInt.unionInt;
#           radioInt.unionByte[0] = (byte)rxPacket[pktPosn];pktPosn++;//10
#           radioInt.unionByte[1] = (byte)rxPacket[pktPosn];pktPosn++;//11
#           offVert = radioInt.unionInt;
#           radioInt.unionByte[0] = (byte)rxPacket[pktPosn];pktPosn++;//12
#           radioInt.unionByte[1] = (byte)rxPacket[pktPosn];pktPosn++;//13
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
#         maxAltitude = (byte)rxPacket[pktPosn];pktPosn++;
#         maxAltitude += ((byte)rxPacket[pktPosn] << 8);pktPosn++;
#         maxVelocity = (byte)rxPacket[pktPosn];pktPosn++;
#         maxVelocity += ((byte)rxPacket[pktPosn] << 8);pktPosn++;
#         maxG = (byte)rxPacket[pktPosn];pktPosn++;
#         maxG += ((byte)rxPacket[pktPosn] << 8);pktPosn++;
#         maxGPSalt = (byte)rxPacket[pktPosn];pktPosn++;
#         maxGPSalt += ((byte)rxPacket[pktPosn] << 8);pktPosn++;
#         GPSlock = (byte)rxPacket[pktPosn];pktPosn++;
#         GPSalt = (byte)rxPacket[pktPosn];pktPosn++;
#         GPSalt += ((byte)rxPacket[pktPosn] << 8);pktPosn++;
#         charGPSlat = (byte)rxPacket[pktPosn];pktPosn++;
#         for(byte i=0;i<4;i++){radioUnion.unionByte[i]=(byte)rxPacket[pktPosn];pktPosn++;}
#         GPSlatitude=radioUnion.GPScoord;
#         charGPSlon = (byte)rxPacket[pktPosn];pktPosn++;
#         for(byte i=0;i<4;i++){radioUnion.unionByte[i]=(byte)rxPacket[pktPosn];pktPosn++;}
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
