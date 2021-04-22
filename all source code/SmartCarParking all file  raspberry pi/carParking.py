import RPi.GPIO as GPIO
from time import sleep
from google.cloud import storage
from firebase import firebase
import imutils
import numpy as np
import pytesseract
import cv2
import time
import os
from PIL import Image

#==============================
# GPIO to LCD mapping
LCD_RS = 26 # Pi pin 26
LCD_E = 24 # Pi pin 24
LCD_D4 = 22 # Pi pin 22
LCD_D5 = 18 # Pi pin 18
LCD_D6 = 16 # Pi pin 16
LCD_D7 = 12 # Pi pin 12

# Device constants
LCD_CHR = True # Character mode
LCD_CMD = False # Command mode
LCD_CHARS = 16 # Characters per line (16 max)
LCD_LINE_1 = 0x80 # LCD memory location for 1st line
LCD_LINE_2 = 0xC0
#===========================================LCD
#======================================PIN

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD) 
servoPin=37
servoPin1=36
GPIO.setup(servoPin,GPIO.OUT)
p=GPIO.PWM(servoPin,50)
p.start(2.5)
GPIO.setup(servoPin1,GPIO.OUT)
q=GPIO.PWM(servoPin1,50)
q.start(2.5)
GPIO.setup(11,GPIO.IN)
GPIO.setup(13,GPIO.IN)
GPIO.setup(15,GPIO.IN)
GPIO.setup(31,GPIO.IN)
GPIO.setup(35,GPIO.OUT) #stop
GPIO.setup(33,GPIO.OUT)  #g



# Use BCM GPIO numbers
GPIO.setup(LCD_E, GPIO.OUT) # Set GPIO's to output mode
GPIO.setup(LCD_RS, GPIO.OUT)
GPIO.setup(LCD_D4, GPIO.OUT)
GPIO.setup(LCD_D5, GPIO.OUT)
GPIO.setup(LCD_D6, GPIO.OUT)
GPIO.setup(LCD_D7, GPIO.OUT)

# Initialize display

#===========================================PIN
#================================Varibales
c1=0
c2=0
f1=0
f2=0
f3=0
f4=0
total_slot=4
in1=0
#space=0
#slot_left=0
exitt=0
countcar=0
slotl=""

#=======================================Variable

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/pi/SmartCarParking/smart-car-parking-system-5d2a7-firebase-adminsdk-lj0km-25cd01718b.json'
firebase = firebase.FirebaseApplication('https://smart-car-parking-system-5d2a7-default-rtdb.firebaseio.com/', None)
client = storage.Client()
bucket = client.get_bucket('smart-car-parking-system-5d2a7.appspot.com')


            
def lcd_init():
     lcd_write(0x33,LCD_CMD) # Initialize
     lcd_write(0x32,LCD_CMD) # Set to 4-bit mode
     lcd_write(0x06,LCD_CMD) # Cursor move direction
     lcd_write(0x0C,LCD_CMD) # Turn cursor off
     lcd_write(0x28,LCD_CMD) # 2 line display
     lcd_write(0x01,LCD_CMD) # Clear display
     time.sleep(0.0005) # Delay to allow commands to process

def lcd_write(bits, mode):
# High bits
     GPIO.output(LCD_RS, mode) # RS

     GPIO.output(LCD_D4, False)
     GPIO.output(LCD_D5, False)
     GPIO.output(LCD_D6, False)
     GPIO.output(LCD_D7, False)
     if bits&0x10==0x10:
         GPIO.output(LCD_D4, True)
     if bits&0x20==0x20:
         GPIO.output(LCD_D5, True)
     if bits&0x40==0x40:
         GPIO.output(LCD_D6, True)
     if bits&0x80==0x80:
         GPIO.output(LCD_D7, True)

# Toggle 'Enable' pin
     lcd_toggle_enable()

    # Low bits
     GPIO.output(LCD_D4, False)
     GPIO.output(LCD_D5, False)
     GPIO.output(LCD_D6, False)
     GPIO.output(LCD_D7, False)
     if bits&0x01==0x01:
         GPIO.output(LCD_D4, True)
     if bits&0x02==0x02:
         GPIO.output(LCD_D5, True)
     if bits&0x04==0x04:
         GPIO.output(LCD_D6, True)
     if bits&0x08==0x08:
         GPIO.output(LCD_D7, True)

# Toggle 'Enable' pin
     lcd_toggle_enable()
     
def lcd_toggle_enable():
     time.sleep(0.0005)
     GPIO.output(LCD_E, True)
     time.sleep(0.0005)
     GPIO.output(LCD_E, False)
     time.sleep(0.0005)

def lcd_text(message,line):
 # Send text to display
     message = message.ljust(LCD_CHARS," ")

     lcd_write(line, LCD_CMD)

     for i in range(LCD_CHARS):
         lcd_write(ord(message[i]),LCD_CHR)     
            

def opencvfunction(carno,mycar):
    try :
        picurl="car"+str(mycar)+".jpg"
        
        #url=bucket.blob(picurl)
        #url.download_to_filename(picurl)
        
        
        img = cv2.imread('car1.jpg',cv2.IMREAD_COLOR)
       
        #img = cv2.imread('car1.jpg',cv2.IMREAD_COLOR)
        #mg = cv2.resize(img, (620,480) )
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #convert to grey scale
        gray = cv2.bilateralFilter(gray, 11, 17, 17) #Blur to reduce noise
        edged = cv2.Canny(gray, 30, 200) #Perform Edge detection
        # find contours in the edged image, keep only the largest
        # ones, and initialize our screen contour
        cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:10]
        screenCnt = None

        # loop over our contours
        for c in cnts:
         # approximate the contour
         peri = cv2.arcLength(c, True)
         approx = cv2.approxPolyDP(c, 0.018 * peri, True)
         
         # if our approximated contour has four points, then
         # we can assume that we have found our screen
         if len(approx) == 4:
          screenCnt = approx
          break

        if screenCnt is None:
         detected = 0
         
        else:
         detected = 1

        if detected == 1:
         cv2.drawContours(img, [screenCnt], -1, (0, 255, 0), 3)

        # Masking the part other than the number plate
        mask = np.zeros(gray.shape,np.uint8)
        new_image = cv2.drawContours(mask,[screenCnt],0,255,-1,)
        new_image = cv2.bitwise_and(img,img,mask=mask)

        # Now crop
        (x, y) = np.where(mask == 255)
        (topx, topy) = (np.min(x), np.min(y))
        (bottomx, bottomy) = (np.max(x), np.max(y))
        Cropped = gray[topx:bottomx+1, topy:bottomy+1]

        #Read the number plate
        text = pytesseract.image_to_string(Cropped, config='--psm 11')
        firebase.put(carno, 'carno', text)
        print("Detected Number is:",text)

        cv2.imshow('image',img)
        cv2.imshow('Cropped',Cropped)

        #cv2.waitKey(0)
        cv2.destroyAllWindows()
    except:
        
        print("hgfh")
while True:
    ir1=GPIO.input(11)
    ir2=GPIO.input(13)
    ir3=GPIO.input(15)
    ir4=GPIO.input(31)
    
    if c1<total_slot:
        print("Conditon1")
        print(ir1)
        if ir1 == 0 and f1==0:
            print("Conditon R1")
            GPIO.output(35, True)
            countcar=in1+1
            #lcd_text(slotl,LCD_LINE_1)
            #lcd_text("Wait...",LCD_LINE_2)
            carno="/carparking/"+"car"+str(countcar)      
            firebase.put(carno, 'detect', 'yes')
            photoupload=firebase.get(carno,'')
            
            if(photoupload['photoupload']=='yes'):
                #opencv
                #lcd_text(slotl,LCD_LINE_1)
                #lcd_text("Veri",LCD_LINE_2)
                opencvfunction(carno,countcar)
                #lcd_text(slotl,LCD_LINE_1)
                #lcd_text("Done",LCD_LINE_2)
                q.ChangeDutyCycle(10)
                time.sleep(0.5)
                GPIO.output(35, False)
                GPIO.output(33, True)
                f1=1
                        
        elif ir2==0 and f1==1:
            print("Conditon R2")
            q.ChangeDutyCycle(2.5)
            time.sleep(1)
            f1=0
            c1=c1+1
            c2=c2+1
            in1=in1+1
            GPIO.output(33, False)
            

    if c2>0:
        print("Conditon2")
        if ir3==0 and f3==0:
            
            p.ChangeDutyCycle(10)
            time.sleep(0.5)
            f3 =1
            f4=1
            ir4=1
            exitt=exitt+1
           
            
        elif ir4 == 0 and f4 ==1:
           
            c2=c2-1
            c1=c1-1
            p.ChangeDutyCycle(2.5)
            time.sleep(0.5)
            f3=0
            f4=0
            #lcd_text("Car Exit",LCD_LINE_2)
            countcar=exitt
            carno="/carparking/"+"car"+str(countcar)      
            firebase.put(carno, 'detect', 'no')
            firebase.put(carno, 'carcheck', 'no')
            firebase.put(carno, 'photoupload', 'no')
            firebase.put(carno, 'carno', '')
            photoupload=firebase.get(carno,'')
            
           
        space=total_slot-in1
        s_left=space+exitt
        slotl="FREE SLOT: "+ str(s_left)
        lcd_text("TOTAL SLOT: 4",LCD_LINE_1)
        lcd_text(slotl,LCD_LINE_2)

#=====================LCD methods
            
            