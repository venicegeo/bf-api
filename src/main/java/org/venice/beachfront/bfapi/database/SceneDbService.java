package org.venice.beachfront.bfapi.database;

import java.sql.SQLException;

import org.joda.time.DateTime;
import org.venice.beachfront.bfapi.database.DbDTO.SceneEntry;

public interface SceneDbService {
	public void insertScene(
			String sceneId,
			DateTime capturedOn,
			String catalogUri,
			double cloudCover,
			String geometryGeoJson,
			int resolution,
			String sensorName
			) throws SQLException;
	
	public SceneEntry getScene(String sceneId) throws SQLException;
}

