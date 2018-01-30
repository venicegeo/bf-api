package org.venice.beachfront.bfapi.database;

import java.sql.SQLException;

import org.joda.time.DateTime;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.DbDTO.SceneEntry;

@Service
public class SceneDbService {
	public void insertScene(String sceneId, DateTime capturedOn, String catalogUri, double cloudCover, String geometryGeoJson,
			int resolution, String sensorName) throws SQLException {
		// TODO
	}

	public SceneEntry getScene(String sceneId) throws SQLException {
		// TODO
		return null;
	}
}
