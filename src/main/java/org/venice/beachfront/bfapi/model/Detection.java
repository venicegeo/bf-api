package org.venice.beachfront.bfapi.model;

import javax.persistence.Column;
import javax.persistence.EmbeddedId;
import javax.persistence.Entity;
import javax.persistence.Table;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.vividsolutions.jts.geom.Geometry;

@Entity
@Table(name = "__beachfront__detection")
public class Detection {
	@EmbeddedId
	private DetectionPK detectionPK;
	@Column(name = "geometry")
	@JsonProperty("geometry")
	private Geometry geometry;

	public Detection() {

	}

	public Detection(Job job, int featureId, Geometry geometry) {
		this.detectionPK = new DetectionPK(job, featureId);
		this.geometry = geometry;
	}

	public DetectionPK getDetectionPK() {
		return detectionPK;
	}

	public void setDetectionPK(DetectionPK detectionPK) {
		this.detectionPK = detectionPK;
	}

	public Geometry getGeometry() {
		return geometry;
	}

	public void setGeometry(Geometry geometry) {
		this.geometry = geometry;
	}
}
