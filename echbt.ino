#include "BLEDevice.h"
#include "device.h"
#include "power.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include "time.h"
#include "esp_sntp.h"
#include "OLEDDisplayUi.h"
#include <Wire.h>
#include "SSD1306Wire.h"


static boolean connected = false;

static BLERemoteCharacteristic* writeCharacteristic;
static BLERemoteCharacteristic* sensorCharacteristic;
static BLEAdvertisedDevice* device;
static BLEClient* client;
static BLEScan* scanner;

const unsigned long ScreenTimeoutMillis = 120000;

static int cadence = 0;
static int resistance = 0;
static int power = 0;
static unsigned long runtime = 0;
static unsigned long last_millis = 0;
static unsigned long last_cadence = 0;
#define KEY_BUILTIN 3
#define LED 2

#define debug 0
#define maxResistance 32
const char *ntpServer1 = "pool.ntp.org";
const char *ntpServer2 = "time.nist.gov";
const long gmtOffset_sec = 3600*-5;
const int daylightOffset_sec = 3600;

const char *time_zone = "CET-1CEST,M3.5.0,M10.5.0/3";  // TimeZone rule for Europe/Rome including daylight adjustment rules (optional)
SSD1306Wire display(0x3c, 5, 4);  // ADDRESS, SDA, SCL  -  SDA and SCL usually populate automatically based on your board's pins_arduino.h e.g. https://github.com/esp8266/Arduino/blob/master/variants/nodemcu/pins_arduino.h
// SH1106Wire display(0x3c, SDA, SCL);

OLEDDisplayUi ui     ( &display );

void drawFrame5(OLEDDisplay *display, OLEDDisplayUiState* state, int16_t x, int16_t y) {
  display->setFont(ArialMT_Plain_10);

  // The coordinates define the left starting point of the text
  display->setTextAlignment(TEXT_ALIGN_LEFT);
  display->drawString(0 + x, 11 + y, "CAD:");
   // The coordinates define the right end of the text
  display->setTextAlignment(TEXT_ALIGN_RIGHT);
  display->drawString(128 + x, 11 + y, "RES:");

  // The coordinates define the center of the text
  display->setTextAlignment(TEXT_ALIGN_CENTER);
  display->drawString(64 + x, 11 + y, "PWR:");

  display->setFont(ArialMT_Plain_24);

  // The coordinates define the left starting point of the text
  display->setTextAlignment(TEXT_ALIGN_LEFT);
  display->drawString(0 + x, 28 + y, String(cadence));
   // The coordinates define the right end of the text
  display->setTextAlignment(TEXT_ALIGN_RIGHT);

  display->drawString(128 + x, 28 + y, String(getPeletonResistance(resistance)));

  // The coordinates define the center of the text
  display->setTextAlignment(TEXT_ALIGN_CENTER);
  display->drawString(64 + x, 28 + y, String(power));

}


String getLocalTime() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    Serial.println("No time available (yet)");
    return"";
  }
  char timeStringBuff[50]; //50 chars should be enough
  strftime(timeStringBuff, sizeof(timeStringBuff), "%B %d %Y %H:%M:%S", &timeinfo);
  String asString(timeStringBuff);
  return(timeStringBuff);
}

// Callback function (gets called when time adjusts via NTP)
void timeavailable(struct timeval *t) {
  Serial.println("Got time adjustment from NTP!");
  Serial.println(getLocalTime());
}

// Called when device sends update notification
static void notifyCallback(BLERemoteCharacteristic* pBLERemoteCharacteristic, uint8_t* data, size_t length, bool isNotify) {
  switch(data[1]) {
    // Cadence notification
    case 0xD1:
      //runtime = int((data[7] << 8) + data[8]); // This runtime has massive drift
      cadence = int((data[9] << 8) + data[10]);
      power = getPower(cadence, resistance);
      break;
    // Resistance notification
    case 0xD2:
      resistance = int(data[3]);
      power = getPower(cadence, resistance);
      break;
  }
  
  if(debug) {
    Serial.print("CALLBACK(");
    Serial.print(pBLERemoteCharacteristic->getUUID().toString().c_str());
    Serial.print(":");
    Serial.print(length);
    Serial.print("):");
    for(int x = 0; x < length; x++) {
      if(data[x] < 16) {
        Serial.print("0");
      }
      Serial.print(data[x], HEX);
    }
    Serial.println();
  }
}

// Called on connect or disconnect
class ClientCallback : public BLEClientCallbacks {
  void onConnect(BLEClient* pclient) {
    digitalWrite(LED,HIGH);
    Serial.println("Connected!");
  }
  void onDisconnect(BLEClient* pclient) {
    connected = false;
    delete(client);
    client = nullptr;
    digitalWrite(LED,LOW);
    Serial.println("Disconnected!");
  }
};

class AdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    Serial.print("BLE Advertised Device found: ");
    Serial.println(advertisedDevice.toString().c_str());
   int stringLength = sizeof(advertisedDevice.getName()) / sizeof(advertisedDevice.getName()[0]);
    if(stringLength > 0) {
      BLEAdvertisedDevice * d = new BLEAdvertisedDevice;
      *d = advertisedDevice;
      addDevice(d);
    }
  }
};
    
void updateDisplay() {
  
  // Runtime
  char buf[5];
  const int minutes = int(runtime / 60000);
  itoa(minutes, buf, 10);

  const int seconds = int(runtime % 60000)/1000;
  if(seconds < 10) {
    buf[0] = '0';
    itoa(seconds, &buf[1], 10);  
  } else {
    itoa(seconds, buf, 10);  
  }
  bool peddling=false;
  String stats="";
if (cadence>0){
  peddling=true;
}
  // Cadence
 
  itoa(cadence, buf, 10);
  Serial.print(buf);
  stats=stats+buf+",";
 

  // Power

  itoa(power, buf, 10);
  Serial.print(buf);
  stats=stats+buf+",";
  

  // Resistance
  itoa(getPeletonResistance(resistance), buf, 10);
  Serial.println(buf);
  stats=stats+buf+",";


String host = "http://<PHP SERVER IP>/";
String file_to_access = "echelon_rtb.php";
String URL = host + file_to_access;
  

 HTTPClient http;


if(peddling){
bool http_begin = http.begin(URL);
 String message_name = "message_sent";
 String message_value = stats+getLocalTime();
 String payload_request = message_name + "=" + message_value;  //Combine the name and value
 http.addHeader("Content-Type", "application/x-www-form-urlencoded");
 int httpResponseCode = http.sendRequest("POST", payload_request);
 //String payload_response = http.getString();
}
}

bool connectToServer() {
  Serial.print("Connecting to ");
  Serial.println(device->getName().c_str());


    
  client = BLEDevice::createClient();
  client->setClientCallbacks(new ClientCallback());
  client->connect(device);

  // Sometimes it immediately disconnects - client will be null if so
  delay(200);
  if(client == nullptr) {
    return false;
  }
  
  BLERemoteService* remoteService = client->getService(connectUUID);
  if (remoteService == nullptr) {
    Serial.print("Failed to find service UUID: ");
    Serial.println(connectUUID.toString().c_str());
    client->disconnect();
    return false;
  }
  Serial.println("Found device.");

  // Look for the sensor
  sensorCharacteristic = remoteService->getCharacteristic(sensorUUID);
  if (sensorCharacteristic == nullptr) {
    Serial.print("Failed to find sensor characteristic UUID: ");
    Serial.println(sensorUUID.toString().c_str());
    client->disconnect();
    return false;
  }
  sensorCharacteristic->registerForNotify(notifyCallback);
  Serial.println("Enabled sensor notifications.");

  // Look for the write service
  writeCharacteristic = remoteService->getCharacteristic(writeUUID);
  if (writeCharacteristic == nullptr) {
    Serial.print("Failed to find write characteristic UUID: ");
    Serial.println(writeUUID.toString().c_str());
    client->disconnect();
    return false;
  }
  // Enable device notifications
  byte message[] = {0xF0, 0xB0, 0x01, 0x01, 0xA2};
  writeCharacteristic->writeValue(message, 5);
  Serial.println("Activated status callbacks.");

  // This will ensure the display comes on initially
  last_cadence = millis();  

  return true;
}
// This array keeps function pointers to all frames
// frames are the single views that slide in
FrameCallback frames[] = { drawFrame5 };

// how many frames are there?
int frameCount = 1;

// Overlays are statically drawn on top of a frame eg. a clock
OverlayCallback overlays[] = { };
int overlaysCount = 0;

void setup() {
  Serial.begin(115200);
  Serial.flush();
  delay(50);
  String ssid="FILL IN";
  String password="FILL IN";
  WiFi.begin(ssid,password); //Connect to WiFi
 
  BLEDevice::init("");
  scanner = BLEDevice::getScan();
  scanner->setAdvertisedDeviceCallbacks(new AdvertisedDeviceCallbacks());
  scanner->setInterval(1349);
  scanner->setWindow(449);
  scanner->setActiveScan(true);

  sntp_set_time_sync_notification_cb(timeavailable);

  /**
   * This will set configured ntp servers and constant TimeZone/daylightOffset
   * should be OK if your time zone does not need to adjust daylightOffset twice a year,
   * in such a case time adjustment won't be handled automagically.
   */
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer1, ntpServer2);

  ui.setTargetFPS(30);
  // Add frames
  ui.setFrames(frames, frameCount);

  // Add overlays
  ui.setOverlays(overlays, overlaysCount);

  // Initialising the UI will init the display too.
  ui.init();

  display.flipScreenVertically();
}

void loop() {
  // Start scan
  
  int remainingTimeBudget = ui.update();
  if (remainingTimeBudget > 0) {
  if(!connected){
    Serial.println("Start Scan!");

    scanner->start(6, false); // Scan for 5 seconds
    BLEDevice::getScan()->stop();

    device = selectDevice(); // Pick a device
    if(device != nullptr) {
      connected = connectToServer();
      if(!connected) {
        Serial.println("Failed to connect...");
        delay(1100);
        return;
      }
    } else {
      Serial.println("No device found...");
      delay(1100);
      return;
    }
  }

  // Update timer if cadence is rolling
  if(cadence > 0) {
    unsigned long now = millis();
    runtime += now - last_millis;
    last_millis = now;
    last_cadence = now;
  } else {
    last_millis = millis();  
  }
  
  delay(remainingTimeBudget); // Delay 200ms between loops.
  updateDisplay();
  }
}
