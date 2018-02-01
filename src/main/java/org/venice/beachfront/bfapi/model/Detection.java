package org.venice.beachfront.bfapi.model;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;

import com.fasterxml.jackson.annotation.JsonProperty;

@Entity
@Table(name = "__beachfront__detection")
public class Detection {
	@Id
	@Column(name = "detection_id")
	@JsonProperty("detection_id")
	private String detectionId;
	@Column(name = "job_id")
	@JsonProperty("job_id")
	private String jobId;
	@Column(name = "user_id")
	@JsonProperty("user_id")
	private String userId;

	public Detection() {

	}

	public Detection(String detectionId, String jobId, String userId) {
		this.detectionId = detectionId;
		this.jobId = jobId;
		this.userId = userId;
	}
}
