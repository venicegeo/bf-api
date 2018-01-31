package org.venice.beachfront.bfapi.database;

import java.sql.SQLException;

import com.vividsolutions.jts.geom.Geometry;
import org.joda.time.DateTime;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.model.Scene;

@Service
public class SceneDbService {
	public void insertScene(String sceneId, DateTime capturedOn, String catalogUri, double cloudCover, Geometry geometry,
			int resolution, String sensorName) throws SQLException {
		// TODO
	}

	public Scene getScene(String sceneId) throws SQLException {
		// TODO
		return null;
	}
}
