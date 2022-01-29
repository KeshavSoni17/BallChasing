from flask import Flask, Response, render_template, request
from datatransfer import datatransfer
from VideoStream import VideoStream
from tracking import tracking
from drawer import drawer
from calculations import *
from functions import *
import keyboard
import math
import cv2
import time


app = Flask(__name__)

camera = VideoStream(getzed()).start()

hsv_values = [6, 244, 147, 19, 255, 255]
parameter_values = [0, 0, 0]
timer = time.time()

track = tracking(hsv_values, parameter_values)
draw = drawer()
def code():
    global timer
    frame_length = 5
    depths = [0]*frame_length
    angles = [0]*frame_length
    exes = [0]*frame_length
    whys = [0]*frame_length

    depth = 0
    angle = 0

    hsv_index = 0
    parameter_index = 0

    while True:
        
        image = camera.read()

        track.update(hsv_values, parameter_values)

        if camera.available():
            height, width, channels = image.shape

            imageR = image[:, :width//2]
            imageL = image[:, width//2:]

            posR, radR, imageRT = track.ball(imageR)
            posL, radL, imageLT = track.ball(imageL)

            depth = find_distance(imageRT, imageLT, posR, posL)
            angle = find_angle(90, height, width, posR, posL)

            depths.append(depth)
            angles.append(angle)
            
            true_x = depth*math.sin(angle*math.pi/180)
            true_y = depth*math.cos(angle*math.pi/180)
            
            change = time.time() - timer
            timer = time.time()
            
            if len(exes) == 1:
                continue
            else:
                velx = abs(true_x - exes[1])/change
                vely = abs(true_y - exes[1])/change

            if len(depths) == frame_length or velx > 60 or vely > 60:
                depths.pop(0)
                angles.pop(0)
                exes.pop(0)
                whys.pop(0)

            result = cv2.bitwise_and(imageR, imageR, mask=imageRT)
            result = draw.circle(result, posR, 5)
            result = draw.text(result, (25, 50), "Angle (degrees): " + str(angle))
            result = draw.text(result, (25, 125), "Distance (inches): " + str(depth))

            #table.send('distance_to_ball', depth)
            #table.send('angle_to_ball', angle)

            imgencode = cv2.imencode('.jpg', result)[1]
            stringData = imgencode.tostring()
            yield (b'--frame\r\n' 
                b'Content-type: text/plain\r\n\r\n' + stringData + b'\r\n')

        if keyboard.is_pressed("enter"): 
            print("Depth (inches): " + str(depth))
            print("Angle (degrees): " + str(angle))
            print("Velocity (x): " + str(velx))
            print("Velocity (y): " + str(vely))
            print(hsv_values)
            print(parameter_values)
        elif keyboard.is_pressed("1"): hsv_index = 0
        elif keyboard.is_pressed("2"): hsv_index = 1
        elif keyboard.is_pressed("3"): hsv_index = 2
        elif keyboard.is_pressed("4"): hsv_index = 3
        elif keyboard.is_pressed("5"): hsv_index = 4
        elif keyboard.is_pressed("6"): hsv_index = 5
        elif keyboard.is_pressed("7"): parameter_index = 0
        elif keyboard.is_pressed("8"): parameter_index = 1
        elif keyboard.is_pressed("9"): parameter_index = 2
        elif keyboard.is_pressed("up arrow"): 
            hsv_values[hsv_index] = hsv_values[hsv_index] + 1
            track.update(hsv_values, parameter_values)
        elif keyboard.is_pressed("down arrow"):
            hsv_values[hsv_index] = hsv_values[hsv_index] - 1
            track.update(hsv_values, parameter_values)
        elif keyboard.is_pressed("w"):
            parameter_values[parameter_index] = parameter_values[parameter_index] + 0.05
            if parameter_values[parameter_index] > 1:
                parameter_values[parameter_index] = 1
            track.update(hsv_values, parameter_values)
        elif keyboard.is_pressed("s"):
            parameter_values[parameter_index] = parameter_values[parameter_index] - 0.05
            if parameter_values[parameter_index] < 0:
                parameter_values[parameter_index] = 0
            track.update(hsv_values, parameter_values)

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        values = [request.form.get("hsv_value_1"), request.form.get("hsv_value_2"), request.form.get("hsv_value_3"), request.form.get("hsv_value_4"), request.form.get("hsv_value_5"), request.form.get("hsv_value_6"), request.form.get("circularity_value"), request.form.get("convexity_value"), request.form.get("intertia_value")]
        for i in range(len(values)):
            if values[i] != None and i<6:
                #pass
                hsv_values[i] = int(values[i])
            elif values[i] != None and i>=6:
                #pass
                parameter_values[i-6] = float(values[i])
        video_feed()
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
   return Response(code(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
   app.run('0.0.0.0', debug = True, port = 5802)
