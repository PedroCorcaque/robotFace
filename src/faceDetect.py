#!/usr/bin/env python3

# import the necessary packages
from imutils.video import VideoStream
import numpy as np
#import argparse
import imutils
import time
import cv2
import rospy
from std_msgs.msg import Float64MultiArray
import map as mp

rospy.init_node("faceDetect", anonymous = False)
pub = rospy.Publisher("updateEyes", Float64MultiArray, queue_size = 10)

# construct the argument parse and parse the arguments
#ap = argparse.ArgumentParser()
#ap.add_argument("-p", "--prototxt", required=True,
#	help="path to Caffe 'deploy' prototxt file")
#ap.add_argument("-m", "--model", required=True,
#	help="path to Caffe pre-trained model")

#args = vars(ap.parse_args())

# load our serialized model from disk
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe("/home/pedro/butia_ws/src/robotFace/src/deploy.prototxt.txt", "/home/pedro/butia_ws/src/robotFace/src/res10_300x300_ssd_iter_140000.caffemodel")

# initialize the video stream and allow the cammera sensor to warmup
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
time.sleep(2.0)

bigger_center = [np.nan, np.nan, np.nan, np.nan]

# loop over the frames from the video stream
while not rospy.is_shutdown():
	# grab the frame from the threaded video stream and resize it
	# to have a maximum width of 400 pixels
	frame = vs.read()

	frame = imutils.resize(frame, width=400)
 
	for angle in np.arange(0, 360, 15):
		rotated = imutils.rotate(frame, 10)

	frame = rotated #[35:565][50:400]

	# grab the frame dimensions and convert it to a blob
	(h, w) = frame.shape[:2]
	blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
		(300, 300), (104.0, 177.0, 123.0))
 
	# pass the blob through the network and obtain the detections and
	# predictions
	net.setInput(blob)
	detections = net.forward()

	big_area = np.nan

	height, width, layers = frame.shape
	img_center = [width/2, height/2]

	# loop over the detections
	for i in range(0, detections.shape[2]):
		# extract the confidence (i.e., probability) associated with the
		# prediction
		confidence = detections[0, 0, i, 2]

		# filter out weak detections by ensuring the `confidence` is
		# greater than the minimum confidence
		if confidence < 0.9:
			continue

		# compute the (x, y)-coordinates of the bounding box for the
		# object
		box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
		(startX, startY, endX, endY) = box.astype("int")
		
		if np.isnan(big_area):
			big_area = (box[2] - box[0]) * (box[3] - box[1])
			bigger_center = box
		else:
			area = (box[2] - box[0]) * (box[3] - box[1])
			if (area > big_area):
				big_area = area
				bigger_center = box

		# draw the bounding box of the face along with the associated
		# probability
		text = "{:.2f}%".format(confidence * 100)
		y = startY - 10 if startY - 10 > 10 else startY + 10
		cv2.rectangle(frame, (startX, startY), (endX, endY),
			(0, 0, 255), 2)
		cv2.putText(frame, text, (startX, y),
			cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)

	msg = Float64MultiArray()
	tamanho = frame.shape
	x = (bigger_center[2] - bigger_center[0])/2 + bigger_center[0]
	y = (bigger_center[3] - bigger_center[1])/2 + bigger_center[1]
	msg.data = [x,y,tamanho[0], tamanho[1]]

	# print(msg.data)

	if not np.isnan(big_area):
		pub.publish(msg)
			
	# show the output frame
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF
 
	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()