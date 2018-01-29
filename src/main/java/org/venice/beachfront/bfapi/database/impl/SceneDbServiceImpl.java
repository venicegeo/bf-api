package org.venice.beachfront.bfapi.database.impl;

import java.io.IOException;
import java.sql.SQLException;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.vividsolutions.jts.geom.Geometry;
import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.SceneDbService;
import org.venice.beachfront.bfapi.database.dao.SceneDao;
import org.venice.beachfront.bfapi.model.Scene;

@Service
public class SceneDbServiceImpl implements SceneDbService {
	@Autowired
	private SceneDao sceneDao;

	public void insertScene(Scene scene) {
		sceneDao.save(scene);
	}
	
	public Scene getScene(String sceneId) {
		return sceneDao.findBySceneId(sceneId);
	}

	@Override
	public boolean sceneExists(String sceneId) throws SQLException {
		return sceneDao.findBySceneId(sceneId) != null;
	}

	@Override
	public void insertScene(String sceneId, DateTime capturedOn, String catalogUri, double cloudCover, Geometry geometry, String sensorName) throws SQLException {
		/*JsonNode geomNode = null;
		try {
			ObjectMapper mapper = new ObjectMapper();
			geomNode = mapper.readTree(geometryGeoJson);
		} catch (IOException e) {
			// Just leave geomNode null but probably log a WARN/ERROR
		}*/
		sceneDao.save(new Scene(
				sceneId,
				capturedOn,
				cloudCover,
				geometry,
				null,
				null,
				null,
				null,
				null,
				sensorName,
				null,
				0.0,
				0.0,
				0.0,
				catalogUri,
				null
		));
	}
}
