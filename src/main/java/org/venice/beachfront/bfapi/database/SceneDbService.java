package org.venice.beachfront.bfapi.database;

import java.sql.SQLException;

import com.vividsolutions.jts.geom.Geometry;
import org.joda.time.DateTime;
import org.venice.beachfront.bfapi.model.Scene;

public interface SceneDbService {
	void insertScene(
			String sceneId,
			DateTime capturedOn,
			String catalogUri,
			double cloudCover,
			Geometry geometry,
			String sensorName
			) throws SQLException;
	void insertScene(Scene scene) throws SQLException;
	Scene getScene(String sceneId) throws SQLException;
	boolean sceneExists(String sceneId) throws SQLException;
}

