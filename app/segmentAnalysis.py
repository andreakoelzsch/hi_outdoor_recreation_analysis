import movingpandas as mpd
import geopandas as gpd

#convert to a line gdf
def convertToLineGDF(data):
    traj = data
    frame = traj.to_line_gdf()
    if frame.crs != None:
        frame = frame.to_crs('EPSG:3857')
    else:
        frame = frame.set_crs('EPSG:3857')
    merged_gdf = frame.dissolve(by='trackId')
    print(merged_gdf)
    print(merged_gdf.columns.to_list())
    print(frame)
    traj = mpd.TrajectoryCollection(frame, "trackId", t="timestamps", crs=frame.crs)
    print(traj)
    exit()