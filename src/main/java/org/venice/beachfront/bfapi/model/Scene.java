package org.venice.beachfront.bfapi.model;

import org.joda.time.DateTime;
import org.springframework.http.MediaType;

import com.fasterxml.jackson.databind.JsonNode;

public class Scene {
	public static final String STATUS_ACTIVE = "active";
	public static final String STATUS_ACTIVATING = "activating";
	public static final String STATUS_INACTIVE = "inactive";
	
	private final String id;
	private final DateTime captureTime;
	private final double cloudCover;
	private final JsonNode geometry;
	private final String imageCoastal;
	private final String imageMultispectral;
	private final String imageSwir1;
	private final String platform;
	private final String resolution;
	private final String sensorName;
	private final String status;
	private final double tide;
	private final double tideMin;
	private final double tideMax;
	private final String uri;
	private final String fileFormat;
	
	public Scene(String id, DateTime captureTime, double cloudCover, JsonNode geometry, String imageCoastal,
			String imageMultispectral, String imageSwir1, String platform, String resolution, String sensorName,
			String status, double tide, double tideMin, double tideMax, String uri, String fileFormat) {
		this.id = id;
		this.captureTime = captureTime;
		this.cloudCover = cloudCover;
		this.geometry = geometry;
		this.imageCoastal = imageCoastal;
		this.imageMultispectral = imageMultispectral;
		this.imageSwir1 = imageSwir1;
		this.platform = platform;
		this.resolution = resolution;
		this.sensorName = sensorName;
		this.status = status;
		this.tide = tide;
		this.tideMin = tideMin;
		this.tideMax = tideMax;
		this.uri = uri;
		this.fileFormat = fileFormat;
	}

	public String getId() {
		return id;
	}

	public DateTime getCaptureTime() {
		return captureTime;
	}

	public double getCloudCover() {
		return cloudCover;
	}

	public JsonNode getGeometry() {
		return geometry;
	}

	public String getImageCoastal() {
		return imageCoastal;
	}

	public String getImageMultispectral() {
		return imageMultispectral;
	}

	public String getImageSwir1() {
		return imageSwir1;
	}

	public String getPlatform() {
		return platform;
	}

	public String getResolution() {
		return resolution;
	}

	public String getSensorName() {
		return sensorName;
	}

	public String getStatus() {
		return status;
	}

	public double getTide() {
		return tide;
	}

	public double getTideMin() {
		return tideMin;
	}

	public double getTideMax() {
		return tideMax;
	}

	public String getUri() {
		return uri;
	}
	
	// ---
	
	public String getExternalId() {
		String[] idParts = this.id.split(":", 1);
		if (idParts.length < 2) {
			throw new RuntimeException("Invalid scene ID: " + this.id);
		}
		return idParts[1];
	}
	
	public String getFileName() {
		switch(this.fileFormat) {
		case "geotiff": return this.getExternalId() + ".tiff";
		case "jpeg2000": return this.getExternalId() + ".jp2";
		default: return this.getExternalId();
		}
	}
	
	public MediaType getMediaType() {
		switch(this.fileFormat) {
		case "geotiff": return new MediaType("image", "tiff");
		case "jpeg2000": return new MediaType("image", "jp2");
		default: return MediaType.APPLICATION_OCTET_STREAM;
		}
	}
	
	public static String parsePlatform(String sceneId) {
		String[] parts = sceneId.split(":", 2);
		if (parts.length < 1) {
			return "";
		}
		return parts[0];	}
	
	public static String parseExternalId(String sceneId) {
		String[] parts = sceneId.split(":", 2);
		if (parts.length < 2) {
			return "";
		}
		return parts[1];
	}

	
}
