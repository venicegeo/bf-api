package org.venice.beachfront.bfapi.model;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;
import javax.persistence.Transient;

import org.hibernate.annotations.Type;
import org.joda.time.DateTime;
import org.springframework.http.MediaType;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.vividsolutions.jts.geom.Geometry;

@Entity
@Table(name = "__beachfront__scene")
public class Scene {
	@Id
	@JsonProperty("scene_id")
	private String sceneId;
	@JsonProperty("captured_on")
	private DateTime captureTime;
	@JsonProperty("cloud_cover")
	private double cloudCover;
	@JsonProperty("geometry")
	//@Column(columnDefinition="Geometry")
	//@Type(type = "org.hibernate.spatial.GeometryType")
	@Type(type = "jts_geometry")
	private Geometry geometry;
	@JsonProperty("image_coastal")
	@Transient
	private String imageCoastal;
	@JsonProperty("image_multispectral")
	@Transient
	private String imageMultispectral;
	@JsonProperty("image_swir1")
	@Transient
	private String imageSwir1;
	@JsonProperty("platform")
	@Transient
	private String platform;
	@JsonProperty("resolution")
	private String resolution;
	@JsonProperty("sensor_name")
	private String sensorName;
	@JsonProperty("status")
	@Transient
	private String status;
	@JsonProperty("tide")
	@Transient
	private double tide;
	@JsonProperty("tide_min")
	@Transient
	private double tideMin;
	@JsonProperty("tide_max")
	@Transient
	private double tideMax;
	@JsonProperty("catalog_uri")
	private String uri;
	@JsonProperty("file_format")
	@Transient
	private String fileFormat;

	/**
	 * Default constructor for Hibernate
	 */
	public Scene() { super(); }

	public Scene(String sceneId, DateTime captureTime, double cloudCover, Geometry geometry, String imageCoastal,
			String imageMultispectral, String imageSwir1, String platform, String resolution, String sensorName,
			String status, double tide, double tideMin, double tideMax, String uri, String fileFormat) {
		this.sceneId = sceneId;
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

	public String getSceneId() {
		return sceneId;
	}

	public void setSceneId(final String sceneId) { this.sceneId = sceneId; }

	public DateTime getCaptureTime() {
		return captureTime;
	}

	public void setCaptureTime(final DateTime captureTime ) {
		this.captureTime = captureTime;
	}

	public double getCloudCover() {
		return cloudCover;
	}

	public void setCloudCover(final double cloudCover ) { this.cloudCover = cloudCover; }

	public Geometry getGeometry() {
		return geometry;
	}

	public void setGeometry(final Geometry geometry) {
		this.geometry = geometry;
	}

	public String getImageCoastal() {
		return imageCoastal;
	}

	public void setImageCoastal(final String imageCoastal) {
		this.imageCoastal = imageCoastal;
	}

	public String getImageMultispectral() {
		return imageMultispectral;
	}

	public void setImageMultispectral(final String imageMultispectral) { this.imageMultispectral = imageMultispectral; }

	public String getImageSwir1() {
		return imageSwir1;
	}

	public void setImageSwir1() { this.imageSwir1 = imageSwir1; }

	public String getPlatform() {
		return platform;
	}

	public void setPlatform(final String platform) { this.platform = platform; }

	public String getResolution() {
		return resolution;
	}

	public void setResolution(final String resolution) {
		this.resolution = resolution;
	}

	public String getSensorName() {
		return sensorName;
	}

	public void setSensorName(final String sensorName) {
		this.sensorName = sensorName;
	}

	public String getStatus() {
		return status;
	}

	public void setStatus(final String status) {
		this.status = status;
	}

	public double getTide() {
		return tide;
	}

	public void setTide(final double tide) { this.tide = tide; }

	public double getTideMin() {
		return tideMin;
	}

	public void setTideMin(final double tideMin) { this.tideMin = tideMin; }

	public double getTideMax() {
		return tideMax;
	}

	public void setTideMax(final double tideMax) { this.tideMax = tideMax; }

	public String getUri() {
		return uri;
	}

	public void setUri(final String uri) {
		this.uri = uri;
	}

	// ---
	
	public String getExternalId() {
		String[] idParts = this.sceneId.split(":", 1);
		if (idParts.length < 2) {
			throw new RuntimeException("Invalid scene ID: " + this.sceneId);
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
	
}
