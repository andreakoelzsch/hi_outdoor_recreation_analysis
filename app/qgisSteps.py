from qgis.core import QgsApplication, QgsRasterLayer, QgsRasterPipe, QgsRectangle, QgsException
import urllib
import numpy as np
import os
import time

#initialize the qgis environment
def qgsAppInit():
    ##set the path to the qgis bin
    try:
        if (os.environ.get('LOCAL_DEV', 'off') == 'on'):
            # local development
            QgsApplication.setPrefixPath("./Library/bin/", True)
        else:
            # running in production (aka on MoveApps)
            # kudos: https://gis.stackexchange.com/a/263853
            os.environ["QT_QPA_PLATFORM"] = "offscreen"
            QgsApplication.setPrefixPath("/usr", False)
    except Exception as e:
        print("Error setting application path. \n" + str(e))

    ##initialize the qgis session
    try:
        qgs = QgsApplication([], False)
        qgs.initQgis()
    except Exception as e:
        print("Error initializing QGIS for analysis. \n" + str(e))

    return qgs

#exit the qgis environment
def qgsAppExit(qgs):
    time.sleep(1)
    qgs.exitQgis()

def getStravaLayer(urlKeysEntry):

    #basic checks for missing elements of the cookie information
    if urlKeysEntry == None:
        print("No information passed. Please input correct parameter and try again. ")
        exit()
    elif (urlKeysEntry.find("Key-Pair-Id") == -1):
        print("Key-Pair-Id incorrect.")
        exit()
    elif (urlKeysEntry.find("Policy") == -1):
        print("Policy incorrect.")
        exit()
    elif (urlKeysEntry.find("Signature") == -1):
        print("Signature incorrect.")
        exit()

    #after the word red, the url needs to be encoded up to the end of the signature key in the cookies
    urlStart = "type=xyz&url=https://heatmap-external-a.strava.com/tiles-auth/all/blue/"
    urlZoomSet = "{z}/{x}/{y}.png"
    urlQ = "?"
    urlKeys = urlKeysEntry
    urlZoomParams = "&zmax=12&zmin=0"

    #configure the url and initialize the conection to Strava
    try:
        #format the url
        url = urlStart + urllib.parse.quote(urlZoomSet) + urlQ + urllib.parse.quote(urlKeys) + urlZoomParams
                
        #create the xyz tile connection
        strava_raster = QgsRasterLayer(url, "Red", "wms")

    except Exception as e:
        print("Error initializing the connection to Strava. \nThere is a problem with the url provided. Please ensure url is formatted correctly and try again.\n" + str(e))
        exit()

    return strava_raster


#get the strava data and the bands of the raster
def extractRasterBands(strava_raster, geoframe):

    #this should always be true
    if (strava_raster.isValid() == True):
        try:
            #set the pipe and provider based on the strava raster layer
            pipe = QgsRasterPipe()
            provider = strava_raster.dataProvider()
            pipe.set(provider.clone())
        except Exception as e:
            print("Error writing file. " + str(e))

        #create a qgs rectangle based on the geoframe
        try:
            input_qgs_rect = QgsRectangle(geoframe.total_bounds[0], geoframe.total_bounds[1], geoframe.total_bounds[2], geoframe.total_bounds[3])
        except Exception as e:
            print("Error obtaining the shapefile. Is it in a shapefile? " + str(e))

        #computes the resolution, should be a whole number
        try:
            pixel_size = 100  #meters (approximately)
            xres = int((input_qgs_rect.xMaximum() - input_qgs_rect.xMinimum()) / pixel_size)
            yres = int((input_qgs_rect.yMaximum() - input_qgs_rect.yMinimum()) / pixel_size)
        except Exception as e:
            print("Error formatting resolution. " + str(e))
            exit()
    else:
        print("Raster layer was invalid, please ensure the url parameters you entered were correct. ")
        exit()

    #block the raster to get the data based on the qgis rectangle
    # this fails if the study areas is too large - threshold for failure is unknown
    try:
        raster_bands = provider.block(1, input_qgs_rect, xres, yres)
    except Exception as e:
        print("Error converting to byte array. " + str(e))
        exit()
    except QgsException as e:
        print("Timer exception. ")
        exit()
    try:
        byte_array = raster_bands.data()
    except Exception as e:
        print("Error converting to byte array. " + str(e))
        exit()

    #convert to a numpy array
    numpy_array = np.frombuffer(byte_array.data(), dtype=np.uint8)
    #reshape the array based on the number of bands
    reshaped_array = np.reshape(numpy_array, (yres, xres, 4))

    return reshaped_array, xres, yres, input_qgs_rect