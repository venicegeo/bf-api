package org.venice.beachfront.bfapi.model;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.IdClass;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.OneToOne;
import javax.persistence.Table;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.vividsolutions.jts.geom.Geometry;
import org.hibernate.annotations.OnDelete;
import org.hibernate.annotations.OnDeleteAction;

@Entity
@IdClass(DetectionPK.class)
@Table(name = "__beachfront__detection")
public class Detection {
	@Id
	@JoinColumn(name = "job_id", nullable = false, columnDefinition = "VARCHAR(64)")
	@OnDelete(action = OnDeleteAction.CASCADE)
	@ManyToOne(targetEntity = Job.class, optional = false)
	@JsonProperty("job_id")
	private Job job;
	@Id
	@Column(name = "feature_id")
	@JsonProperty("feature_id")
	private String featureId;
	@Column(name = "geometry")
	@JsonProperty("geometry")
	private Geometry geometry;

	public Detection() {

	}

	public Detection(Job job, String featureId, Geometry geometry) {
		this.job = job;
		this.featureId = featureId;
		this.geometry = geometry;
	}

	public Job getJob() {
		return job;
	}

	public void setJob(Job job) {
		this.job = job;
	}

	public String getFeatureId() {
		return featureId;
	}

	public void setFeatureId(String featureId) {
		this.featureId = featureId;
	}

	public Geometry getGeometry() {
		return geometry;
	}

	public void setGeometry(Geometry geometry) {
		this.geometry = geometry;
	}
}
