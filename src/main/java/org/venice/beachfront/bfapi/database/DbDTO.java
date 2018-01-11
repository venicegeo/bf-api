package org.venice.beachfront.bfapi.database;

import org.joda.time.DateTime;

public class DbDTO {
	public static class JobEntry {
		public String jobId;
		public String name;
		public String algorithmName;
		public String algorithmVersion;
		public String createdBy;
		public DateTime createdOn;
		public String status;
		public double tide;
		public double tideMin24h;
		public double tideMax24h;
		public Boolean computeMask;
		public String errorMessage;
		public String executionStep;
		public SceneEntry scene;
	}
	
	public static class JobStatusEntry {
		public String jobId;
		public String status;
	}

	public static class SceneEntry {
		public String sceneId;
		public DateTime capturedOn;
		public String catalogUri;
		public double cloudCover;
		public String sensorName;
		public String geometryGeoJson;
	}
	
	public static class UserEntry {
		public String userId;
		public String userName;
		public String apiKey;
		public DateTime createdOn;
	}
}
