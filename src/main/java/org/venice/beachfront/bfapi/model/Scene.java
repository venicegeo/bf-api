package org.venice.beachfront.bfapi.model;

import javax.persistence.Column;
import javax.persistence.Convert;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;
import javax.persistence.Transient;

import org.hibernate.annotations.Type;
import org.joda.time.DateTime;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.vividsolutions.jts.geom.Geometry;

@Entity
@Table(name = "__beachfront__scene")
public class Scene {
	public static final String PLATFORM_PLANETSCOPE = "planetscope";
	public static final String PLATFORM_RAPIDEYE = "rapideye";
	public static final String PLATFORM_SENTINEL = "landsat";
	public static final String PLATFORM_LANDSAT = "sentinel";

	public static final String STATUS_ACTIVE = "active";
	public static final String STATUS_ACTIVATING = "activating";
	public static final String STATUS_INACTIVE = "inactive";

	@Id
	@Column(name = "scene_id")
	@JsonProperty("scene_id")
	private String sceneId;
	@Convert(converter = TimestampConverter.class)
	@Column(name = "captured_on")
	@JsonProperty("captured_on")
	private DateTime captureTime;
	@Column(name = "cloud_cover")
	@JsonProperty("cloud_cover")
	private double cloudCover;
	@Column(name = "geometry")
	@JsonProperty("geometry")
	// @Column(columnDefinition="Geometry")
	// @Type(type = "org.hibernate.spatial.GeometryType")
	@Type(type = "jts_geometry")
	private Geometry geometry;
	@Column(name = "resolution")
	@JsonProperty("resolution")
	private int resolution;
	@Column(name = "sensor_name")
	@JsonProperty("sensor_name")
	private String sensorName;
	@Column(name = "catalog_uri")
	@JsonProperty("catalog_uri")
	private String uri;

	@Transient
	@Column(name = "tide")
	@JsonProperty("tide")
	private Double tide;
	@Transient
	@Column(name = "tide_min_24h")
	@JsonProperty("tide_min_24h")
	private Double tideMin24H;
	@Transient
	@Column(name = "tide_max_24h")
	@JsonProperty("tide_max_24h")
	private Double tideMax24H;

	/**
	 * Default constructor for Hibernate
	 */
	public Scene() {
		super();
	}

	public Scene(String sceneId, DateTime captureTime, double cloudCover, Geometry geometry, int resolution, String sensorName,
			String uri) {
		this.sceneId = sceneId;
		this.captureTime = captureTime;
		this.cloudCover = cloudCover;
		this.geometry = geometry;
		this.resolution = resolution;
		this.sensorName = sensorName;
		this.uri = uri;
	}

	public String getSceneId() {
		return sceneId;
	}

	public void setSceneId(final String sceneId) {
		this.sceneId = sceneId;
	}

	public DateTime getCaptureTime() {
		return captureTime;
	}

	public void setCaptureTime(final DateTime captureTime) {
		this.captureTime = captureTime;
	}

	public double getCloudCover() {
		return cloudCover;
	}

	public void setCloudCover(final double cloudCover) {
		this.cloudCover = cloudCover;
	}

	public Geometry getGeometry() {
		return geometry;
	}

	public void setGeometry(final Geometry geometry) {
		this.geometry = geometry;
	}

	public int getResolution() {
		return resolution;
	}

	public void setResolution(final int resolution) {
		this.resolution = resolution;
	}

	public String getSensorName() {
		return sensorName;
	}

	public void setSensorName(final String sensorName) {
		this.sensorName = sensorName;
	}

	public String getUri() {
		return uri;
	}

	public void setUri(final String uri) {
		this.uri = uri;
	}

	public String getExternalId() {
		String[] idParts = this.sceneId.split(":", 1);
		if (idParts.length < 2) {
			throw new RuntimeException("Invalid scene ID: " + this.sceneId);
		}
		return idParts[1];
	}

	public static String parsePlatform(String sceneId) {
		String[] parts = sceneId.split(":", 2);
		if (parts.length < 1) {
			return "";
		}
		return parts[0];
	}

	public static String parseExternalId(String sceneId) {
		String[] parts = sceneId.split(":", 2);
		if (parts.length < 2) {
			return "";
		}
		return parts[1];
	}

	public Double getTide() {
		return tide;
	}

	public void setTide(Double tide) {
		this.tide = tide;
	}

	public Double getTideMin24H() {
		return tideMin24H;
	}

	public void setTideMin24H(Double tideMin24H) {
		this.tideMin24H = tideMin24H;
	}

	public Double getTideMax24H() {
		return tideMax24H;
	}

	public void setTideMax24H(Double tideMax24H) {
		this.tideMax24H = tideMax24H;
	}
}
