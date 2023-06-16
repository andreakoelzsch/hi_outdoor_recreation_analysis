import movingpandas as mpd
import geopandas as gpd
import numpy as np
from rtree import index
from shapely.geometry import Point, MultiLineString
import math

#convert to a line gdf
def convertToLineGDF(data):
    traj = data
    frame = traj.to_line_gdf()
    crs_frame = traj.to_point_gdf()

    crsf = crs_frame.crs
    frame = frame.set_crs(crsf)

    if frame.crs.to_epsg() != 3857:
        frame = frame.to_crs('EPSG:3857')
    else:
        frame = frame
    frame = frame.dissolve(by='trackId').reset_index()
    if ((int(frame.total_bounds[2]) - int(frame.total_bounds[0])) > 500000) | ((int(frame.total_bounds[3]) - int(frame.total_bounds[1])) > 500000):
        print("Study size is too large, please subset your data to an area smaller than 500,000 metres by 500,000 metres and try again. Try using a smaller number of individuals from the dataset. ")
        exit()
    return frame

#perform operations on the array to format it for the TrajectoryCollection
def cellPointArray(geoframe, reshaped_array, xres, yres, input_qgs_rect):           

    #get the crs of the original geoframe to return it to the user as it was given
    geo_crs = geoframe.crs

    #compute the appropriate pixel size
    pixel_x_size = (input_qgs_rect.xMaximum() - input_qgs_rect.xMinimum()) / (reshaped_array.shape[1])
    pixel_y_size = (input_qgs_rect.yMaximum() - input_qgs_rect.yMinimum()) / (reshaped_array.shape[0])
    xmin = input_qgs_rect.xMinimum()
    ymin = input_qgs_rect.yMinimum()
    data = []

    #make a grid of x and y coordinates
    x_coords = np.arange(0, xres) * pixel_x_size + xmin
    y_coords = np.arange(yres - 1, -1, -1) * pixel_y_size + ymin

    #create a meshgrid
    x_mesh, y_mesh = np.meshgrid(x_coords, y_coords)

    #flatten into 1D arrays
    x_flattened = x_mesh.flatten()
    y_flattened = y_mesh.flatten()

    #calculate midpoints
    x_midpoints = x_flattened + (pixel_x_size / 2)
    y_midpoints = y_flattened + (pixel_y_size / 2)

    #create shapely points
    geometries = [Point(x, y) for x, y in zip(x_midpoints, y_midpoints)]

    #create a dictionary:key set for the bands
    band_data = {
            'band_1': reshaped_array[:, :, 2].flatten(),
            'band_2': reshaped_array[:, :, 1].flatten(),
            'band_3': reshaped_array[:, :, 0].flatten(),
            'band_4': reshaped_array[:, :, 3].flatten()
        }

    #append the geometry and band data to a geodataframe
    data = {'geometry': geometries, **band_data}
    df = gpd.GeoDataFrame(data, crs=geo_crs)

    # remove rows with missing geometry
    df = df[~df['geometry'].isnull()]

    #reproject just in case
    if df.crs != 'EPSG:3857':
        df = df.to_crs('EPSG:3857')

    return df, pixel_x_size, pixel_y_size

#combine the dataframes together
def computePointNearest(bandGdf, geoframe, pixel_x_size, pixel_y_size):
    #this is not working correctly, it is not what I want
    print(geoframe)
    idx = index.Index()
    for i, geometry in enumerate(geoframe['geometry']):
        print(i)
        idx.insert(i, geometry.bounds)
    distance_threshold = 75.0
    point_counts = []
    count = 0
    print(len(bandGdf))
    for point in bandGdf['geometry']:
        print(count, end='')
        candidate_indices = list(idx.intersection(point.buffer(distance_threshold).bounds))
        candidate_multilinestrings = geoframe.loc[candidate_indices]

        # Perform the actual distance check
        within_distance_mask = candidate_multilinestrings['geometry'].distance(point) <= distance_threshold

        # Count the number of points within the distance threshold
        point_count = sum(within_distance_mask)
        point_counts.append(point_count)
        print('\r', end='')
        count += 1
    geoframe['point_count'] = point_counts
    print(geoframe)
    exit()
    return geoframe




# merged_gdf = frame.dissolve(by='trackId').reset_index()
# merged_gdf['t'] = merged_gdf['t'].dt.strftime('%Y-%m-%d %H:%M:%S')
# merged_gdf['timestamps'] = merged_gdf['timestamps'].dt.strftime('%Y-%m-%d %H:%M:%S')
# merged_gdf['prev_t'] = merged_gdf['prev_t'].dt.strftime('%Y-%m-%d %H:%M:%S')

# print(merged_gdf.crs)

# traj = mpd.TrajectoryCollection(frame, "trackId", t="timestamps", crs=frame.crs)
# print(traj)
# exit()