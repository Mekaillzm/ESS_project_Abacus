# ESS

The ESS system simulates environmental data in real-time, all while gathering subjective local views as well.

This is coupled with a robust predictive system that uses past data to simulate what locals would be expected to feel.
This immediate detection enables operators to act quickly, addressing issues before they escalate into broader dissatisfaction or tourist decline.


# SETUP

1. InfluxDB

The following buckets must be set up in InfluxDB v 2.x or above for the code to work correctly. 
InfluxDB must be added as a data source in Grafana as well. 

Access information has been included below, but this is for a local Docker container instance of InfluxDB. A new setup will require updated credentials that may or may not match the ones below.

Organisation name: abacus-demo
This organisation name has been used by Grafana and Node-RED to access the buckets outlined below.

Username: amdin
Password: admin123

The username may appear to be a typo at first glance, but it is not.

Names of working buckets:
-islamabadAQI
-islabadFeelsLike
-islamabadPredictions
-islamabadWeather
-karachiAQI
-karachiFeelsLike
-karachiPredictions
-lahoreAQI
-lahoreWeather
-lahorePredictions
-lahoreFeelsLike

On the InfluxDB web UI, you can upload the sample data as well; however, this may not work as the data contains past timestamps.


2. Node-RED

In your Node-RED dashboard, select Import and paste the code from flows.json.

Go to the Flow "Influx to Python" and select the Node "Set url". Set msg.url to the url that flask_post_data2.py is active on. 
This varies by the network used and can be obtained upon running flask_post_data2.py, after which it will appear in the output screen.

For example, if the address is  http://0.0.0.0:5000/
Then enter the url:  http://0.0.0.0:5000/postData

Secondly, random number generators have been enabled to post pseudo-random user views. You may disable these by disabling the following nodes in "Flutter to Influx"
Nodes to disable: "Random general View Generator", "False Data Generator"
These do not impact the functionality of the Flutter app.

Thirdly, ensure InfluxDB has been set up as outlined in Influx_setup.txt

Finally, press deploy on all four flows.

3. Flutter

The code/flutter folder contains code for the Flutter android app

It has been on the Android 16.0 using an Android Studio based virtual machine.
The entire folder can be downloaded for use on Android Studio directly, after installation as outlined here: https://docs.flutter.dev/get-started/install

When running, use the main.dart file for execution, and ensure all assets, code files and prerequisites are installed as well in the folder structure provided.
Prerequisite extensions (available on Android Studio):
-Flutter
-Dart
-http

4. Scikit Learn Model Setup

First, install the prerequisite Pyhton libraries (and Pyhton 3, if it is not already installed)
They are all available with pip.

Prerequisite libraries:
1. pandas
2. flask
3. sklearn
4. numpy

Installation commands:
pip install pandas numpy scikit-learn
pip install flask

Secondly, download all the code in the code/scikit-learn folder, keeping all code within the same folder. Ensuring a stable WiFi connection, run flusk_post_data2.py.

Thirdly, check the code output (e.g. on a terminal) for its active URLs.
An example of the expected output is, "Running on http://0.0.0.0:5000"
Copy one and write it in the following format:
 http://0.0.0.0:5000/postData

Paste this as outlined in the Node-RED setup instructions.

5. Grafana setup

When setting up Grafana, do the following:

Create a data source called "inlfuxdb".
Important: Select Flux as the query language.

Use your credentials for InlfuxDB.
For reference, the previously used credentials are included below, though these are only valid on the original Docker container.

InfluxDB credentials:
Organisation: abacus-demo
Username: amdin
Password: admin123

Ensure all the required buckets have been created in influxDB, as outlined by Influx_setup_info.txt

Once done, create a new Dashboard.
Go to Settings > JSON model
Paste all code from model.json
Press save dashboard

Select a suitable refresh time and time window for the dashboard, based on how much past data you would like to see.

6. Testing

Deploy and run all Flows one by one in Node-RED. If the wifi connection is stable, they should work as expected, and the Grafana Dashboard will update with visuals.


